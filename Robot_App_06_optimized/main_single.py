# ==================== AI Assistant System ====================
# Single-thread voice assistant (no threading, no queues, no SystemState)
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
from local_commands import handle_local_command
import eye_runner as eye
import pygame
import os
import re
import sys
import time
import traceback

from Config import Config

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

# ------------------- Main Function -------------------
def main():
    pygame.init()

    print("=" * 60)
    print("🚀 AI Assistant (Single-Thread, No SystemState) Starting...")
    print("=" * 60)
    print("Say 'stop' or 'خلاص' to cancel speaking.")
    print("=" * 60)

    speak_safe("Hello, I'm ready to help you.")

    listening = True
    active = True
    last_status = time.time()

    while active:
        try:
            
            print("ℹ️ Listening..." if listening else "⏸️ Paused. Say 'wake up' to resume.")

            if not listening:
                print("❌ not listening")
                time.sleep(0.1)
                continue

            # --- 1) Record ---
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
                print("❌ there is no user_input")
                continue

            print(f"\n🎤 User: {user_input}")

            # --- 3) Stop Command ---
            if is_stop_command(user_input):
                try:
                    tts.interrupt()
                except Exception:
                    pass
                print("⚠️ Stop command detected, cancelled speech.")
                continue

            # --- 4) Local Commands ---
            try:
                should_continue, local_response, action, _ = handle_local_command(user_input)
                print(f"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            except Exception as ex:
                print(f"❌ Local command error: {ex}")
                traceback.print_exc()
                should_continue, local_response, action = True, None, None

            if action == 'pause':
                listening = False
                print("💤 System paused.")
            elif action == 'resume':
                listening = True
                print("✅ System resumed.")
            # [Check]
            if local_response:
                print(f"🤖 Local Response: {local_response}")
                speak_safe(local_response)
            
            # --- 5) AI Processing ---
            if should_continue and listening:
                try:
                    print("🤔 Processing with AI...")
                    ai_response = n8n.chat("123456", user_input)
                    if ai_response:
                        print(f"🤖 AI Response: {ai_response}")
                        speak_safe(ai_response)
                except Exception as ex:
                    print(f"❌ AI error: {ex}")
                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n⛔ KeyboardInterrupt: stopping assistant.")
            active = False
        except Exception as loop_ex:
            print(f"❌ Loop error: {loop_ex}")
            traceback.print_exc()
            time.sleep(0.2)

    cleanup()
    print("✅ System stopped successfully.")

# ------------------- Entry Point -------------------
if __name__ == "__main__":
    main()
