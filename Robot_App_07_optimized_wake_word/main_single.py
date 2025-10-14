# ==================== AI Assistant System ====================
# Single-thread voice assistant (no threading)
# Wake Word: Ziko / زيكو
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
from local_commands import handle_local_command, extract_after_wake  # <== NEW
#import eye_runner as eye
import pygame
import os
import re
import sys
import time
import traceback
import threading
from queue import Queue, Empty

from Config import Config

# ================= System State Manager =================
class SystemState:
    """
    Thread-safe system state manager
    Handles listening state, speaking state, and interruptions
    """
    def __init__(self):
        self.is_listening = True
        self.is_active = True
        self.is_speaking = False
        self.lock = threading.Lock()
    
    def pause_listening(self):
        """Pause the listening state"""
        with self.lock:
            self.is_listening = False
    
    def resume_listening(self):
        """Resume the listening state"""
        with self.lock:
            self.is_listening = True
    
    def should_listen(self):
        """Check if system should be listening"""
        with self.lock:
            return self.is_listening and self.is_active
    
    def stop_system(self):
        """Stop the entire system"""
        with self.lock:
            self.is_active = False
    
    def set_speaking(self, speaking):
        """Set the speaking state"""
        with self.lock:
            self.is_speaking = speaking
    
    def get_speaking(self):
        """Get the current speaking state"""
        with self.lock:
            return self.is_speaking
    
    def interrupt(self):
        """Interrupt the system and stop all running processes"""
        with self.lock:
            print("\n⚠️ INTERRUPT: User is speaking - stopping all processes...")
            # Stop audio immediately
            tts.interrupt()
            # Clear all queues
            self.clear_all_queues()
            self.is_speaking = False
            print("✅ All processes stopped, ready for new input")
    
    def clear_all_queues(self):
        """Clear all communication queues"""
        # Clear tts_queue
        while not tts_queue.empty():
            try:
                tts_queue.get_nowait()
            except Empty:
                break

# ------------------- Queues for Thread Communication -------------------
audio_queue = Queue(maxsize=3)
tts_queue = Queue(maxsize=3)
system_state = SystemState()

def safe_put(q, item):
    try:
        q.put_nowait(item)
    except:
        try: q.get_nowait()  # drop oldest
        except Empty: pass
        q.put_nowait(item)

# ------------------- Environment Setup -------------------
if sys.platform.startswith("linux"):
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", "/home/pi/.Xauthority")
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# ------------------- Initialize Components -------------------
recorder = AudioRecorder()
stt = SpeechToText()
tts = TextToSpeech()
n8n = N8nClient()
config = Config()
system_is_active = True

# ------------------- Arabic normalization helpers -------------------
_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def _normalize_ar(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = _AR_DIACRITICS.sub('', text)
    text = text.replace('ـ', '')
    for src in 'أإآٱ':
        text = text.replace(src, 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')  # <== ensure yaa-maqsoora normalized
    return text

STOP_TOKENS = [
    "stop","end","cancel","enough","quit","exit","abort","halt",
    "قف","توقف","وقف","بس","خلص","خلاص","كفايه","كفاية",
    "ستوب","وقف التشغيل","اسكت","كفا","خلصنا","خلاص كده",
]
_BOUNDARY = r'(?:\s|$|[^\w\u0600-\u06FF])'
STOP_RE = re.compile(r'^\s*(?:' + '|'.join(map(re.escape, STOP_TOKENS)) + r')' + _BOUNDARY, re.IGNORECASE)

def is_stop_command(text: str) -> bool:
    if not text:
        return False
    return bool(STOP_RE.search(text) or STOP_RE.search(_normalize_ar(text)))

# ------------------- Utility Methods -------------------
def speak_safe(text: str):
    """Speak safely with basic interruption handling."""
    if not text:
        return
    try:
        tts.interrupt()
    except Exception:
        pass
    try:
        tts.say(text)
    except Exception as ex:
        print(f"❌ Speech error: {ex}")

def cleanup():
    """Cleanup resources gracefully."""
    try:
        eye.cleanup()
    except Exception:
        pass
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

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for audio to finish playing
        pygame.time.Clock().tick(5)

# ------------------- Main Function -------------------
def main_thread():
    # pygame.init()

    print("="*60)
    print("🚀 AI Assistant Started — Wake Word: Ziko / زيكو")
    print("="*60)
    print("Say 'Ziko ...' or 'زيكو ...' to issue a command.")
    print("Say 'stop' or 'توقف' anytime to cancel.")
    print("="*60)

    play_sound("Resources/voice_msgs/soli_welcome.wav")

    listening = True
    last_status = time.time()
    is_first_time=True
    while system_state.is_active:
        try:
            if not is_first_time:
                play_sound("Resources/voice_msgs/listening.wav")
                print("ℹ️ Listening..." if listening else "⏸️ Paused. Say 'wake up' to resume.")
            is_first_time = False
            if not listening:
                print("❌ not listening")
                time.sleep(0.1)
                continue

            # 1) Record
            audio_buffer = recorder.record_until_silence(
                max_duration=25.0,
                noise_calib_duration=0.8,
                start_frames=3,
                end_frames=15,            # جَرّب 18-22 لو لسه بيقطع
                post_silence_hold=0.35,
                pre_roll_ms=350,
                min_speech_after_start=1.8,
                threshold_boost=3.0       # قللها لو ما بيلتقطش أصوات منخفضة
            )
            if not audio_buffer:
                print("❌ there is no audio_buffer")
                continue

            # --- 2) Speech to Text ---
            try:
                user_input = stt.transcribe_bytes(audio_buffer)
            except Exception as ex:
                print(f"❌ STT error: {ex}")
                continue
            if not user_input:
                continue

            print(f"\n🎤 User: {user_input}")

            # 3) Safety stop (works without wake word)
            if is_stop_command(user_input):
                try:
                    tts.interrupt()
                except Exception:
                    pass
                print("⚠️ Stop command detected, cancelled speech.")
                continue

            # 4) Enforce wake word (Novi/نوفي variants)
            has_wake, remainder, wake_form = extract_after_wake(user_input)
            if not has_wake:
                print("⏭️ Ignored (no wake word).")
                # اختياري: تشغيل نغمة خفيفة تدل إن النظام لم يلتقط نداء نوفي
                # play_sound("Resources/voice_msgs/need_wake.wav")
                continue

            # لو النداء فقط بدون أمر
            if not remainder:
                play_sound("Resources/voice_msgs/yes_how_help.wav")
                continue

            # 5) Local commands THEN AI (using the remainder only)
            try:
                should_continue, local_response, action, pass_text = handle_local_command(remainder)
                print(f"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            except Exception as ex:
                print(f"❌ Local command error: {ex}")
                traceback.print_exc()
                should_continue, local_response, action, pass_text = True, None, None, remainder

            if action == 'pause':
                listening = False
                print("💤 System paused.")
            elif action == 'resume':
                listening = True
                print("✅ System resumed.")

            if local_response:
                print(f"🤖 Local Response: {local_response}")
                speak_safe(local_response)

            if should_continue and listening:
                try:
                    safe_put(tts_queue, "Resources/voice_msgs/thinking.wav")
                    print("🤔 Processing with AI...")
                    # NOTE: pass_text (if greetings trimmed) else remainder
                    prompt_text = pass_text if pass_text else remainder
                    ai_response = n8n.chat("123456", prompt_text)
                    if ai_response:
                        print(f"🤖 AI Response: {ai_response}")
                        safe_put(tts_queue, "Resources/voice_msgs/got_it.wav")
                        speak_safe(ai_response)
                except Exception as ex:
                    print(f"❌ AI error: {ex}")
                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n⛔ KeyboardInterrupt: stopping assistant.")
            break
        except Exception as loop_ex:
            print(f"❌ Loop error: {loop_ex}")
            traceback.print_exc()
            time.sleep(0.2)

    cleanup()
    print("✅ System stopped successfully.")

def text_to_speech_thread():
    while system_state.is_active:
        try:
            text = tts_queue.get(timeout=1)
            if text:
                print(f"\n🤖 tts: {text}")
                system_state.set_speaking(True)
                play_sound(text)
                system_state.set_speaking(False)
                print("✅ Finished speaking\n")
        except Empty:
            continue
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
            system_state.set_speaking(False)
        finally:
            system_state.set_speaking(False)

# ================= Main Function =================
def main():
    pygame.init()

    # Create and start threads
    threads = [
        threading.Thread(target=text_to_speech_thread, daemon=True, name="TextToSpeech"),
        threading.Thread(target=main_thread, daemon=True, name="main_thread")
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
        print(f"✅ Started: {thread.name}")

    print("\n" + "=" * 60)
    print("✅ System ready! Start with 'Novi ...' or 'نوفي ...'")
    print("💡 Tip: You can interrupt anytime by speaking while I'm talking")
    print("=" * 60 + "\n")

    # Keep main thread alive
    try:
        while system_state.is_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⛔ Shutting down system...")
        system_state.stop_system()
        cleanup()
        

        # tracker.closeAllWindows()
        
        print("✅ System stopped successfully")
        print("=" * 60)

# ------------------- Entry Point -------------------
if __name__ == "__main__":
    main()
