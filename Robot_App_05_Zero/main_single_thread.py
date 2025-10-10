# main_single_thread.py
# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
import text_to_speech as tts
import ai_n8n as llm
import pygame
import time
from local_commands import handle_local_command
# ملاحظة: تم حذف أي استخدام لـ face_tracker / video_eye_player لتجنب الحلقات المتزامنة

# ------------------- System State -------------------
class SystemState:
    def __init__(self):
        self.is_active = True
        self.is_listening = True

    def pause_listening(self):
        self.is_listening = False

    def resume_listening(self):
        self.is_listening = True

    def stop_system(self):
        self.is_active = False

# ------------------- Init -------------------
recorder = AudioRecorder()
stt = SpeechToText()
system_state = SystemState()

# ------------------- Helpers -------------------
def speak(text: str):
    if not text:
        return
    print(f"\n🤖 Response: {text}")
    tts.text_to_speech(text)

def banner():
    print("=" * 60)
    print("🚀 AI Assistant (Single-Thread) Starting...")
    print("=" * 60)
    print("\n📋 Available Local Commands (No API):")
    print("  • Greetings: 'hello', 'hi', 'مرحبا', 'هلا'")
    print("  • Pause: 'bye', 'goodbye', 'مع السلامة', 'sleep mode'")
    print("  • Resume: 'wake up', 'استيقظ', 'are you there'")
    print("  • Time: 'what time is it', 'كم الساعة'")
    print("  • Date: 'what date is it', 'ما التاريخ'")
    print("  • Thanks: 'thank you', 'شكرا'")
    print("  • Help: 'help', 'مساعدة'")
    print("  • Exit: Ctrl+C")
    print("=" * 60)

# ------------------- Main Loop (Single Thread) -------------------
def main():
    pygame.init()
    banner()
    speak("Hello, I'm ready to help you.")

    try:
        while system_state.is_active:
            if not system_state.is_listening:
                print("💤 System paused - say a resume command (e.g., 'wake up').")
            # 1) تسجيل حتى الصمت
            try:
                audio_buffer = recorder.record_until_silence(
                    silence_threshold=500,
                    silence_duration=1.5,
                    max_duration=20
                )
            except Exception as rec_err:
                print(f"Recording error: {rec_err}")
                time.sleep(1)
                continue

            # 2) تحويل الكلام لنص
            try:
                user_input = stt.convert(audio_buffer)
            except Exception as conv_err:
                print(f"Conversion error: {conv_err}")
                continue

            if not user_input:
                # لا يوجد كلام مفهوم؛ كرر الحلقة
                continue

            print(f"\n📝 User: {user_input}")

            # 3) أوامر محلية أولاً
            try:
                should_continue, local_response, action, _ = handle_local_command(user_input)
                print(f"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            except Exception as local_err:
                print(f"Local command error: {local_err}")
                should_continue, local_response, action = True, None, None

            # 3.1) إدارة الحالة (إيقاف/استئناف)
            if action == 'pause':
                system_state.pause_listening()
                print("💤 System paused.")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ System resumed.")

            # 3.2) الرد المحلي إن وُجد
            if local_response:
                speak(local_response)
                continue

            # 4) لو مسموح نكمل وبنستمع حالياً، نرسل للـ LLM
            if should_continue and system_state.is_listening:
                try:
                    print("🤔 Processing with AI...")
                    response = llm.chat(user_input)
                    print(response)
                    speak(response)
                except Exception as ai_err:
                    print(f"AI processing error: {ai_err}")
                    continue
            else:
                # لو السيستم متوقف عن الاستماع، ندي تلميح بسيط
                if not system_state.is_listening:
                    speak("I'm paused. Say 'wake up' to resume.")

            # 5) مهلة صغيرة قبل الدورة التالية
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⛔ Shutting down system...")
    finally:
        system_state.stop_system()
        try:
            tts.stop_speech()
        except Exception:
            pass
        print("✅ System stopped successfully")
        print("=" * 60)

if __name__ == "__main__":
    main()
