# ==================== AI Assistant System ====================
# Single-thread voice assistant (main loop) + one TTS/sound thread
# Wake Word: Ziko / زيكو
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
from local_commands import handle_local_command, extract_after_wake
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
# صوت واحد فقط يُشغَّل في خيط واحد (الـ TTS/sound worker)
tts_queue = Queue(maxsize=5)      # يحمل إما مسار ملف WAV أو نص TTS
audio_queue = Queue(maxsize=3)    # احتياطي لو استخدمته لاحقاً

def safe_put(q, item):
    try:
        q.put_nowait(item)
    except:
        try: q.get_nowait()   # drop oldest
        except Empty: pass
        q.put_nowait(item)

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
    text = text.replace('ى', 'ي')
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
    n = _normalize_ar(text)
    return bool(STOP_RE.search(text) or STOP_RE.search(n))

# ------------------- TTS + Sound Abstraction -------------------
class SpeechBus:
    """
    قناة موحّدة لتشغيل:
    - ملفات WAV عبر pygame.mixer
    - نصوص TTS عبر محرك tts.say()
    في خيط واحد فقط لمنع التضارب.
    """
    def __init__(self, tts):
        self.tts = tts
        self.lock = threading.Lock()

    def speak_text(self, text: str):
        if not text:
            return
        safe_put(tts_queue, {"kind": "tts", "data": text})

    def play_wav(self, path: str):
        if not path:
            return
        safe_put(tts_queue, {"kind": "wav", "data": path})

# ------------------- System State Manager -------------------
class SystemState:
    def __init__(self, tts_bus: SpeechBus):
        self._is_listening = True
        self._is_active = True
        self._is_speaking = False
        self.lock = threading.Lock()
        self.tts_bus = tts_bus

    # listening
    def pause_listening(self):
        with self.lock:
            self._is_listening = False

    def resume_listening(self):
        with self.lock:
            self._is_listening = True

    def should_listen(self):
        with self.lock:
            return self._is_listening and self._is_active

    # speaking
    def set_speaking(self, speaking: bool):
        with self.lock:
            self._is_speaking = speaking

    def is_speaking(self) -> bool:
        with self.lock:
            return self._is_speaking

    # lifecycle
    def stop_system(self):
        with self.lock:
            self._is_active = False

    @property
    def is_active(self):
        with self.lock:
            return self._is_active

    def interrupt(self):
        with self.lock:
            print("\n⚠️ INTERRUPT: user speaking - stopping all outputs...")
            # تفريغ الطابور لإيقاف أي أصوات لاحقة
            while not tts_queue.empty():
                try:
                    tts_queue.get_nowait()
                except Empty:
                    break
            # إيقاف الـ TTS الجاري (لو محركك يدعم interrupt فهو داخل TextToSpeech)
            try:
                self.tts_bus.tts.interrupt()
            except Exception:
                pass
            self._is_speaking = False
            print("✅ outputs cancelled")

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

speech_bus = SpeechBus(tts)
system_state = SystemState(speech_bus)

# ------------------- Helpers -------------------
def cleanup():
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
    العامل الوحيد الذي يشغّل الصوت:
    - إذا kind=wav: يشغّل الملف
    - إذا kind=tts: ينطق النص عبر tts.say()
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

            kind = item.get("kind")
            data = item.get("data")
            if kind == "wav":
                system_state.set_speaking(True)
                print(f"🔊 [SND] {data}")
                pygame.mixer.music.load(data)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and system_state.is_active:
                    clock.tick(20)
                system_state.set_speaking(False)

            elif kind == "tts":
                txt = data or ""
                if txt.strip():
                    system_state.set_speaking(True)
                    print(f"🗣️ [TTS] {txt}")
                    # تأكد أن أي تشغيل قديم توقف
                    try: tts.interrupt()
                    except Exception: pass
                    try:
                        tts.say(txt)
                    except Exception as ex:
                        print(f"❌ Speech error: {ex}")
                    system_state.set_speaking(False)
        except Exception as ex:
            print(f"❌ tts_worker error: {ex}")
            system_state.set_speaking(False)

# ------------------- Main Loop -------------------
def main_loop():
    print("="*60)
    print("🚀 AI Assistant — Wake Word: Ziko / زيكو")
    print("="*60)
    print("Say: 'Ziko ...' or 'زيكو ...' to issue a command.")
    print("Say: 'stop' or 'توقف' anytime to cancel.")
    print("="*60)

    # أصوات افتتاحية/مؤشرات
    # غيّر المسارات بما يناسب ملفاتك
    speech_bus.play_wav("Resources/voice_msgs/welcome.wav")

    # ابدأ بالاستماع
    system_state.resume_listening()

    first_cycle = True
    while system_state.is_active:
        try:
            if not system_state.should_listen():
                time.sleep(0.15)
                continue

            if not first_cycle:
                speech_bus.play_wav("Resources/voice_msgs/listening.wav")
            first_cycle = False

            # 1) تسجيل
            audio_buffer = recorder.record_until_silence(
                max_duration=25.0,
                noise_calib_duration=0.8,
                start_frames=3,
                end_frames=15,
                post_silence_hold=0.35,
                pre_roll_ms=350,
                min_speech_after_start=1.8,
                threshold_boost=3.0
            )
            if not audio_buffer:
                # لا يوجد كلام مفهوم
                continue

            # 2) STT
            try:
                user_input = stt.transcribe_bytes(audio_buffer)
            except Exception as ex:
                print(f"❌ STT error: {ex}")
                continue

            if not user_input:
                continue

            print(f"\n🎤 User: {user_input}")

            # 3) أوامر الإيقاف (لا تحتاج نداء)
            if is_stop_command(user_input):
                system_state.interrupt()
                print("⚠️ Stop detected.")
                continue

            # 4) نداء Ziko/زيكو فقط
            has_wake, remainder, wake_form = extract_after_wake(user_input)  # تأكد أن هذه تدعم 'Ziko/زيكو'
            if not has_wake:
                print("⏭️ Ignored (no wake word).")
                continue

            if not remainder:
                # نداء فقط بدون أمر
                speech_bus.play_wav("Resources/voice_msgs/yes_how_help.wav")
                continue

            # 5) أوامر محلية أولاً
            try:
                should_continue, local_response, action, pass_text = handle_local_command(remainder)
                print(f"local: continue={should_continue}, action={action}, resp={local_response}")
            except Exception as ex:
                print(f"❌ Local command error: {ex}")
                traceback.print_exc()
                should_continue, local_response, action, pass_text = True, None, None, remainder

            if action == 'pause':
                system_state.pause_listening()
                print("💤 Paused listening.")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ Resumed listening.")

            if local_response:
                speech_bus.speak_text(local_response)

            # 6) إن احتجنا AI
            if should_continue and system_state.should_listen():
                safe_put(tts_queue, {"kind":"wav","data":"Resources/voice_msgs/thinking.wav"})
                print("🤔 Processing with AI...")
                prompt_text = pass_text if pass_text else remainder
                try:
                    ai_response = n8n.chat("123456", prompt_text)
                except Exception as ex:
                    print(f"❌ AI error: {ex}")
                    ai_response = None

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
def main():
    pygame.init()
    try:
        pygame.mixer.init()  # تأكد من تهيئة الميكسـر
    except Exception as ex:
        print(f"⚠️ pygame.mixer.init failed: {ex}")

    # تشغيل عمال الصوت
    tts_thread = threading.Thread(target=tts_worker, daemon=True, name="TTS-Worker")
    tts_thread.start()
    print("✅ Started: TTS-Worker")

    print("\n" + "=" * 60)
    print("✅ System ready! Start with 'Ziko ...' or 'زيكو ...'")
    print("💡 Tip: You can interrupt me any time by just saying 'stop/توقف'.")
    print("=" * 60 + "\n")

    try:
        main_loop()
    finally:
        # إيقاف نظيف
        system_state.stop_system()
        time.sleep(0.2)
        cleanup()
        print("✅ System stopped successfully.")

if __name__ == "__main__":
    main()
