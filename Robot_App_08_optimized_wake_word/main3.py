# ==================== AI Assistant System ====================
# Single-thread main loop + TTS/Sound worker + Barge-in listener
# Wake Word: Ziko / زيكو
# =============================================================
#
# FILE GOALS
# ----------
# - Keep listening "always-on" to allow barge-in (user can say stop anytime).
# - Accept stop commands either directly ("stop", "وقف") or after wake word ("Ziko stop", "زيكو وقف").
# - Use a single audio output worker (one thread) to avoid mixer/TTS race conditions.
# - Clean cancellation: if user interrupts while speaking/thinking, we stop audio and ignore late AI results.
#
# MAIN COMPONENTS
# ---------------
# 1) SystemState: Thread-safe states + interrupt signalling + AI cancel versioning.
# 2) SpeechBus: A thin abstraction over a single queue (tts_queue) handling WAV/ TTS requests.
# 3) tts_worker: The ONLY thread that plays audio (WAV) or speaks (TTS). It observes interrupts.
# 4) barge_in_listener: An always-on short-window listener to detect stop commands while speaking/thinking.
# 5) main_loop: The primary loop to capture full utterances, enforce wake word, run local commands, then AI.
#
# EXTERNAL DEPENDENCIES (you already have them in your project)
# ------------------------------------------------------------
# - AudioRecorder.record_until_silence(...) returns raw audio bytes for STT.
# - SpeechToText.transcribe_bytes(audio_bytes) returns a text transcription.
# - TextToSpeech.say(text) speaks; TextToSpeech.interrupt() stops speaking now.
# - N8nClient.chat(session_id, text) returns AI response text.
# - local_commands_ultra_fast.extract_after_wake(text) -> (has_wake, remainder, wake_form)
# - local_commands_ultra_fast.handle_local_command(text) -> (should_continue, local_response, action, pass_text)
#
# NOTE
# ----
# - Update Resources/voice_msgs/*.wav paths to match your files.
# - Ensure extract_after_wake recognizes "Ziko/زيكو" (and variants if desired).
# - All comments are in English per your preference.

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
from local_commands_ultra_fast import handle_local_command, extract_after_wake
import pygame
import os
import re
import sys
import time
import traceback
import threading
from queue import Queue, Empty

from Config import Config

# ------------------- Queues -------------------
# tts_queue carries both WAV and TTS tasks via {"kind": "wav"/"tts", "data": ...}
# Only the tts_worker thread should touch pygame.mixer/music and TTS engine.
tts_queue = Queue(maxsize=5)
# Optional auxiliary queue (reserved if you later need audio jobs)
audio_queue = Queue(maxsize=3)

def safe_put(q, item):
    """
    Enqueue item without blocking. If the queue is full, drop the oldest item.
    This avoids deadlocks when multiple quick events (e.g., many chimes) arrive.
    """
    try:
        q.put_nowait(item)
    except:
        try:
            q.get_nowait()  # drop oldest
        except Empty:
            pass
        q.put_nowait(item)

# ------------------- Arabic normalization -------------------
# We normalize Arabic input to make stop-word detection resilient to diacritics/variants.
_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def _normalize_ar(text: str) -> str:
    """
    Lowercases, strips diacritics/elongations, and normalizes common Arabic letter variants.
    """
    if not text:
        return ""
    text = text.strip().lower()
    text = _AR_DIACRITICS.sub('', text)
    text = text.replace('ـ', '')      # kashida
    for src in 'أإآٱ':
        text = text.replace(src, 'ا')  # alef variants -> alef
    text = text.replace('ة', 'ه')      # ta marboota -> ha
    text = text.replace('ى', 'ي')      # alef maqsura -> ya
    return text

# Stop tokens accepted at the start of an utterance (after optional wake word).
STOP_TOKENS = [
    # English
    "stop", "end", "cancel", "enough", "quit", "exit", "abort", "halt",
    # Arabic (common forms)
    "قف", "توقف", "وقف", "بس", "خلص", "خلاص", "كفايه", "كفاية",
    "ستوب", "وقف التشغيل", "اسكت", "كفا", "خلصنا", "خلاص كده",
]

# Boundary pattern: allow stop token followed by whitespace, EOS, or non-word char.
_BOUNDARY = r'(?:\s|$|[^\w\u0600-\u06FF])'
# Regex matches any stop token at the *beginning* of string (after possible spaces).
STOP_RE = re.compile(r'^\s*(?:' + '|'.join(map(re.escape, STOP_TOKENS)) + r')' + _BOUNDARY, re.IGNORECASE)

def is_stop_command(text: str) -> bool:
    """
    True if the text begins with a stop token (Arabic or English).
    We also test after Arabic normalization to catch minor spelling variants.
    """
    if not text:
        return False
    n = _normalize_ar(text)
    return bool(STOP_RE.search(text) or STOP_RE.search(n))

def is_stop_with_optional_wake(text: str) -> bool:
    """
    True if the input is a stop command either:
    - directly (e.g., "stop", "وقف"), OR
    - after a wake word (e.g., "Ziko stop", "زيكو وقف").
    """
    if not text:
        return False
    try:
        has_wake, remainder, _wake = extract_after_wake(text)
    except Exception:
        has_wake, remainder = False, None
    candidate = remainder if has_wake else text
    return is_stop_command(candidate)

# ------------------- TTS + Sound Abstraction -------------------
class SpeechBus:
    """
    A unified channel to submit audio output tasks:
    - play WAV files via pygame.mixer (kind="wav")
    - speak text via TTS engine (kind="tts")
    Only the tts_worker should dequeue and execute them.
    """
    def __init__(self, tts):
        self.tts = tts
        self.lock = threading.Lock()

    def speak_text(self, text: str):
        """Queue a TTS job; handled by tts_worker."""
        if not text:
            return
        safe_put(tts_queue, {"kind": "tts", "data": text})

    def play_wav(self, path: str):
        """Queue a WAV playback job; handled by tts_worker."""
        if not path:
            return
        safe_put(tts_queue, {"kind": "wav", "data": path})

# ------------------- System State Manager -------------------
class SystemState:
    """
    Thread-safe manager for system lifecycle and interruption signals.

    - _is_listening: whether main_loop should capture/handle user utterances.
    - _is_active: overall running flag for all threads.
    - _is_speaking: true while audio (WAV/TTS) is being output.
    - interrupt_event: raised on user barge-in; tells audio worker to stop immediately.
    - _ai_cancel_version: increments on each interrupt; used to drop late AI results.
    """
    def __init__(self, tts_bus: "SpeechBus"):
        self._is_listening = True
        self._is_active = True
        self._is_speaking = False
        self.lock = threading.Lock()
        self.tts_bus = tts_bus

        # Interruption & AI-cancel versioning
        self.interrupt_event = threading.Event()
        self._ai_cancel_version = 0  # increment on every interrupt

    # Listening controls
    def pause_listening(self):
        with self.lock:
            self._is_listening = False

    def resume_listening(self):
        with self.lock:
            self._is_listening = True

    def should_listen(self):
        with self.lock:
            return self._is_listening and self._is_active

    # Speaking flag (for UI/diagnostics)
    def set_speaking(self, speaking: bool):
        with self.lock:
            self._is_speaking = speaking

    def is_speaking(self) -> bool:
        with self.lock:
            return self._is_speaking

    # Lifecycle
    def stop_system(self):
        with self.lock:
            self._is_active = False

    @property
    def is_active(self):
        with self.lock:
            return self._is_active

    # AI-cancel version: capture before AI call, compare after AI returns.
    def current_ai_version(self) -> int:
        with self.lock:
            return self._ai_cancel_version

    def was_ai_cancelled(self, version: int) -> bool:
        with self.lock:
            return version != self._ai_cancel_version

    def clear_interrupt(self):
        """Clear the current interrupt flag before starting a new audio task."""
        self.interrupt_event.clear()

    def interrupt(self):
        """
        Handle user barge-in (e.g., user says 'stop' while speaking/thinking):
        - Signal 'interrupt_event' to stop current audio immediately.
        - Increment AI cancel version to ignore any pending AI results.
        - Stop TTS engine and pygame music now.
        - Purge queued audio tasks (ding/got_it).
        """
        # Keep lock short to minimize latency
        with self.lock:
            print("\n⚠️ INTERRUPT: user speaking - cancel outputs & current tasks...")
            self._ai_cancel_version += 1
            self.interrupt_event.set()
            self._is_speaking = False

        # Purge queued audio tasks so no more sounds follow the interrupt.
        try:
            while not tts_queue.empty():
                tts_queue.get_nowait()
        except Empty:
            pass

        # Stop speaking/music immediately
        try:
            self.tts_bus.tts.interrupt()
        except Exception:
            pass
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        print("✅ interrupted. Ready for new input.")

# ------------------- Environment Setup -------------------
# Configure X/Qt vars when running on Linux (e.g., Raspberry Pi / desktop Linux)
if sys.platform.startswith("linux"):
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", "/home/pi/.Xauthority")
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# ------------------- Initialize Components -------------------
# Instantiate your I/O/AI components (from your existing project).
recorder = AudioRecorder()
stt = SpeechToText()
tts = TextToSpeech()
n8n = N8nClient()
config = Config()

# Create speech bus and system state after TTS is ready.
speech_bus = SpeechBus(tts)
system_state = SystemState(speech_bus)

# ------------------- Cleanup -------------------
def cleanup():
    """
    Gracefully release audio and STT/TTS resources.
    Always call in finally or at shutdown to avoid locked devices.
    """
    try:
        recorder.close()
    except Exception:
        pass
    try:
        tts.interrupt()
        tts.cleanup()
    except Exception:
        pass
    try:
        stt.cleanup()
    except Exception:
        pass
    try:
        pygame.mixer.quit()
        pygame.quit()
    except Exception:
        pass

# ------------------- Workers -------------------
def tts_worker():
    """
    The ONLY thread that outputs audio:
    - kind="wav": play a WAV file via pygame.mixer.music.
    - kind="tts": speak text via TTS engine (tts.say).
    The worker continuously checks 'interrupt_event' while playing.
    """
    clock = pygame.time.Clock()
    while system_state.is_active:
        try:
            item = tts_queue.get(timeout=0.5)
        except Empty:
            continue

        try:
            if not item:
                continue

            # Each task starts with a clean interrupt flag (if set previously).
            system_state.clear_interrupt()
            kind = item.get("kind")
            data = item.get("data")

            if kind == "wav":
                # Play a short indicator sound (listening/thinking/got_it/welcome, etc.)
                system_state.set_speaking(True)
                print(f"🔊 [SND] {data}")
                pygame.mixer.music.load(data)
                pygame.mixer.music.play()

                # While WAV is playing, break immediately on interrupt.
                while pygame.mixer.music.get_busy() and system_state.is_active:
                    if system_state.interrupt_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    clock.tick(30)

                system_state.set_speaking(False)

            elif kind == "tts":
                # Speak natural language with your TTS engine.
                txt = (data or "").strip()
                if txt:
                    system_state.set_speaking(True)
                    print(f"🗣️ [TTS] {txt}")
                    try:
                        # Ensure any prior speech is cancelled before starting.
                        if system_state.interrupt_event.is_set():
                            system_state.clear_interrupt()
                        tts.interrupt()
                        # Start speaking; if an interrupt occurs, tts.interrupt() will be called by SystemState.
                        tts.say(txt)
                    except Exception as ex:
                        print(f"❌ Speech error: {ex}")
                    finally:
                        system_state.set_speaking(False)

        except Exception as ex:
            print(f"❌ tts_worker error: {ex}")
            system_state.set_speaking(False)

barge_in_listener_status=False
def barge_in_listener():
    """
    Always-on short-window listener for 'stop' (with/without wake word).
    - Records tiny windows (~1.0–1.5s) to detect "stop"/"توقف" even while speaking or waiting for AI.
    - If detected, triggers SystemState.interrupt() immediately and plays a short 'cancelled' chime.
    - Keeps CPU usage reasonable by sleeping briefly between empty windows.
    """
    while system_state.is_active:
        try:
            # Small capture window: fast turnaround and low latency.
            audio_buf = recorder.record_until_silence(
                max_duration=1.3,          # small window (tune 1.0–1.5s)
                noise_calib_duration=0.0,  # no calibration per window to keep latency low
                start_frames=2,
                end_frames=8,
                post_silence_hold=0.0,
                pre_roll_ms=200,
                min_speech_after_start=0.2,
                threshold_boost=0.0
            )
            if not audio_buf:
                # No voice activity detected in this small window.
                time.sleep(0.05)
                continue

            # Transcribe the small window. Use the same STT engine.
            try:
                partial = stt.transcribe_bytes(audio_buf)
            except Exception:
                # If STT fails for a tiny chunk, just skip silently.
                continue

            if not partial:
                continue

            # If user said a stop command (with/without wake), interrupt immediately.
            if is_stop_with_optional_wake(partial):
                system_state.interrupt()
                print("🛑 BARGE-IN: stop detected (with/without wake).")
                safe_put(tts_queue, {"kind": "wav", "data": "Resources/voice_msgs/cancelled.wav"})
                system_state.resume_listening()
                # Small back-off to avoid retriggering on the same audio chunk.
                time.sleep(0.3)

        except Exception:
            # Soft-fail to keep the barge-in listener robust.
            time.sleep(0.1)

# ------------------- Main Loop -------------------
def main_loop():
    """
    The primary (single-thread) loop:
    1) Record a full utterance (longer window) until silence.
    2) Transcribe (STT).
    3) Handle stop (with/without wake) -> immediate interrupt.
    4) Enforce wake word (Ziko/زيكو). Ignore if absent.
    5) Run local commands first; then AI if needed.
    6) Speak responses via speech_bus (queued to tts_worker).
    """
    print("="*60)
    print("🚀 AI Assistant — Wake Word: Ziko / زيكو")
    print("="*60)
    print("Say: 'Ziko ...' or 'زيكو ...' to issue a command.")
    print("Say: 'stop' or 'توقف' anytime to cancel (with or without wake).")
    print("="*60)

    # Play a welcome chime (adjust to your assets).
    speech_bus.play_wav("Resources/voice_msgs/welcome.wav")

    # Start in listening mode.
    system_state.resume_listening()
    first_cycle = True

    while system_state.is_active:
        try:
            # If temporarily paused (via local 'pause' action), don't record.
            if not system_state.should_listen():
                time.sleep(0.15)
                continue

            # Optional listening chime (skip for the first cycle to avoid clutter).
            if not first_cycle:
                speech_bus.play_wav("Resources/voice_msgs/listening.wav")
            first_cycle = False

            # 1) Capture a full utterance with comfortable end-of-speech defaults.
            audio_buffer = recorder.record_until_silence(
                max_duration=25.0,        # overall limit for a user command
                noise_calib_duration=0.8, # do a bit of noise calibration for main utterances
                start_frames=3,
                end_frames=15,            # tune (18–22) if you get premature cut-offs
                post_silence_hold=0.35,
                pre_roll_ms=350,
                min_speech_after_start=1.8,
                threshold_boost=3.0
            )
            if not audio_buffer:
                # Nothing intelligible this cycle.
                continue

            # 2) Transcribe the captured utterance.
            try:
                user_input = stt.transcribe_bytes(audio_buffer)
            except Exception as ex:
                print(f"❌ STT error: {ex}")
                continue

            if not user_input:
                continue

            print(f"\n🎤 User: {user_input}")

            # 3) Stop command (direct or after wake) does not require wake in main loop either.
            if is_stop_with_optional_wake(user_input):
                system_state.interrupt()
                print("⚠️ Stop detected.")
                continue

            # 4) Enforce wake word (Ziko/زيكو) for functional commands.
            has_wake, remainder, wake_form = extract_after_wake(user_input)
            if not has_wake:
                print("⏭️ Ignored (no wake word).")
                continue

            if not remainder:
                # User only said "Ziko" without a command -> prompt gently.
                speech_bus.play_wav("Resources/voice_msgs/yes_how_help.wav")
                continue

            # 5) Local commands first (volume, pause/resume, greetings, time, etc.)
            try:
                should_continue, local_response, action, pass_text = handle_local_command(remainder)
                print(f"local: continue={should_continue}, action={action}, resp={local_response}")
            except Exception as ex:
                print(f"❌ Local command error: {ex}")
                traceback.print_exc()
                should_continue, local_response, action, pass_text = True, None, None, remainder
            '''
            # Apply local actions to listening state if any.
            if action == 'pause':
                system_state.pause_listening()
                print("💤 Paused listening.")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ Resumed listening.")
            '''
            # Speak local response if present (e.g., "Volume set", "Okay, pausing").
            if local_response:
                speech_bus.speak_text(local_response)


            # 6) If still needed, query AI (N8n) with the processed text.
            if should_continue and system_state.should_listen():
                safe_put(tts_queue, {"kind":"wav","data":"Resources/voice_msgs/thinking.wav"})
                
                if not barge_listener_thread.is_alive():
                    barge_listener_thread.run()

                print("🤔 Processing with AI...")
                prompt_text = pass_text if pass_text else remainder

                # Capture AI cancel version. If an interrupt happens, version increments.
                ai_version = system_state.current_ai_version()
                try:
                    ai_response = n8n.chat("123456", prompt_text)
                except Exception as ex:
                    print(f"❌ AI error: {ex}")
                    ai_response = None

                # If interrupted while waiting for AI, drop late results.
                if system_state.was_ai_cancelled(ai_version):
                    print("⛔ AI response ignored due to interrupt.")
                    ai_response = None

                # Speak AI response if still valid.
                if ai_response:
                    print(f"🤖 AI: {ai_response}")
                    safe_put(tts_queue, {"kind":"wav","data":"Resources/voice_msgs/got_it.wav"})
                    speech_bus.speak_text(ai_response)

        except KeyboardInterrupt:
            print("\n⛔ KeyboardInterrupt — stopping.")
            break
        except Exception as ex:
            print(f"❌ Loop error: {ex}")
            traceback.print_exc()
            time.sleep(0.25)

# ------------------- Entry Point -------------------
barge_listener_thread = threading.Thread(target=barge_in_listener, daemon=True, name="Barge-In")

def main():
    """
    Bootstraps pygame mixer, starts the audio worker and barge-in listener, then runs main loop.
    """
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception as ex:
        print(f"⚠️ pygame.mixer.init failed: {ex}")

    # Start audio output worker (WAV + TTS in one place).
    tts_thread = threading.Thread(target=tts_worker, daemon=True, name="TTS-Worker")
    tts_thread.start()
    print("✅ Started: TTS-Worker")

    # Start barge-in listener (tiny windows to catch "stop" anytime).
    barge_listener_thread.start()
    print("✅ Started: Barge-In")

    print("\n" + "=" * 60)
    print("✅ System ready! Start with 'Ziko ...' or 'زيكو ...'")
    print("💡 Tip: Say 'stop/توقف' anytime — even while I'm talking.")
    print("=" * 60 + "\n")

    try:
        main_loop()
    finally:
        # Ensure all threads exit cleanly.
        system_state.stop_system()
        time.sleep(0.2)
        cleanup()
        print("✅ System stopped successfully.")

if __name__ == "__main__":
    main()
