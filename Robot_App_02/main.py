# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
import text_to_speech as tts
import ai_model as llm
import pygame
import threading
from queue import Queue

# Create objects
recorder = AudioRecorder()
stt = SpeechToText()

# Queues للتواصل بين الـ threads
audio_queue = Queue()
text_queue = Queue()
response_queue = Queue()

def audio_recording_thread():
    """Thread مخصص لتسجيل الصوت"""
    while True:
        try:
            audio_buffer = recorder.record_until_silence(
                silence_threshold=500,
                silence_duration=1.5,  # تقليل وقت الانتظار
                max_duration=20
            )
            audio_queue.put(audio_buffer)
        except Exception as e:
            print(f"خطأ في التسجيل: {e}")

def speech_to_text_thread():
    """Thread مخصص لتحويل الصوت لنص"""
    while True:
        try:
            audio_buffer = audio_queue.get()
            user_input = stt.convert(audio_buffer)
            
            if user_input:
                print(f"📝 المستخدم: {user_input}")
                text_queue.put(user_input)
        except Exception as e:
            print(f"خطأ في التحويل: {e}")

def ai_processing_thread():
    """Thread مخصص لمعالجة النصوص والرد"""
    while True:
        try:
            user_input = text_queue.get()
            response = llm.chat(user_input)
            response_queue.put(response)
        except Exception as e:
            print(f"خطأ في المعالجة: {e}")

def text_to_speech_thread():
    """Thread مخصص لتحويل النص لصوت"""
    while True:
        try:
            response = response_queue.get()
            print(f"🤖 الرد: {response}")
            tts.text_to_speech(response)
        except Exception as e:
            print(f"خطأ في التحويل للصوت: {e}")

def main():
    """Main function with threading"""
    pygame.init()
    
    print("🚀 بدء النظام...")
    tts.text_to_speech("مرحباً، كيف يمكنني مساعدتك اليوم؟")
    
    # إنشاء وتشغيل الـ threads
    threads = [
        threading.Thread(target=audio_recording_thread, daemon=True),
        threading.Thread(target=speech_to_text_thread, daemon=True),
        threading.Thread(target=ai_processing_thread, daemon=True),
        threading.Thread(target=text_to_speech_thread, daemon=True)
    ]
    
    for thread in threads:
        thread.start()
    
    print("✅ النظام جاهز! ابدأ الحديث...")
    
    # Keep main thread alive
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n⛔ إيقاف النظام...")

if __name__ == "__main__":
    main()
