# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
import text_to_speech as tts
import ai_n8n as llm
import pygame
import threading
from queue import Queue, Empty
import time
from local_commands import handle_local_command
import face_tracker as tracker
import video_eye_player as eye
import os

os.environ.setdefault("DISPLAY", ":0")
os.environ.setdefault("XAUTHORITY", "/home/pi/.Xauthority")
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# Create objects
recorder = AudioRecorder()
stt = SpeechToText()

# Queues for thread communication
audio_queue = Queue()
text_queue = Queue()
response_queue = Queue()

# System state
class SystemState:
    def __init__(self):
        self.is_listening = True
        self.is_active = True
        self.is_speaking = False  # جديد: لتتبع حالة التحدث
        self.lock = threading.Lock()
    
    def pause_listening(self):
        with self.lock:
            self.is_listening = False
    
    def resume_listening(self):
        with self.lock:
            self.is_listening = True
    
    def should_listen(self):
        with self.lock:
            return self.is_listening and self.is_active
    
    def stop_system(self):
        with self.lock:
            self.is_active = False
    
    def set_speaking(self, speaking):
        with self.lock:
            self.is_speaking = speaking
    
    def get_speaking(self):
        with self.lock:
            return self.is_speaking
    
    def interrupt(self):
        """مقاطعة النظام وإيقاف كل العمليات الجارية"""
        with self.lock:
            print("\n⚠️ INTERRUPT: User is speaking - stopping all processes...")
            # إيقاف الصوت فورًا
            tts.stop_speech()
            # تفريغ جميع الطوابير
            self.clear_all_queues()
            self.is_speaking = False
            print("✅ All processes stopped, ready for new input")
    
    def clear_all_queues(self):
        """تفريغ جميع الطوابير"""
        # تفريغ audio_queue
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except Empty:
                break
        
        # تفريغ text_queue
        while not text_queue.empty():
            try:
                text_queue.get_nowait()
            except Empty:
                break
        
        # تفريغ response_queue
        while not response_queue.empty():
            try:
                response_queue.get_nowait()
            except Empty:
                break

system_state = SystemState()

def audio_recording_thread():
    """خيط مخصص لتسجيل الصوت مع كشف المقاطعة"""
    while system_state.is_active:
        try:
            # التسجيل المستمر
            audio_buffer = recorder.record_until_silence(
                silence_threshold=500,
                silence_duration=1.5,
                max_duration=20
            )
            '''
            # هنوقف هنا بحيث انه يتم ايقاف باقي ال queues فقط في حالة وجود text
            # إذا كان النظام يتحدث، هذا يعني مقاطعة!
            if system_state.get_speaking():
                print("\n🔴 INTERRUPT DETECTED!")
                system_state.interrupt()
            '''
            audio_queue.put(audio_buffer)
            
        except Exception as e:
            print(f"Recording error: {e}")
            time.sleep(1)

def speech_to_text_thread():
    """خيط مخصص لتحويل الصوت إلى نص"""
    while system_state.is_active:
        try:
            audio_buffer = audio_queue.get(timeout=1)
            user_input = stt.convert(audio_buffer)
            
            if user_input:
                print(f"\n📝 User: {user_input}")
                system_state.interrupt()
                text_queue.put(user_input)
                
        except Empty:
            continue
        except Exception as e:
            print(f"Conversion error: {e}")

def ai_processing_thread():
    """خيط مخصص لمعالجة الذكاء الاصطناعي"""
    while system_state.is_active:
        try:
            user_input = text_queue.get(timeout=1)
            
            # فحص الأوامر المحلية أولاً
            should_continue, local_response, action, x = handle_local_command(user_input)
            print(F"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            # معالجة تغييرات الحالة
            if action == 'pause':
                system_state.pause_listening()
                print("💤 System paused - waiting for wake up command...")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ System resumed - ready to help!")
            
            # إرسال الاستجابة
            if local_response:
                response_queue.put(local_response)
            elif should_continue and system_state.should_listen():
                print("🤔 Processing with AI...")
                response = llm.chat(user_input)
                response_queue.put(response)
                print(response)
            
        except Empty:
            continue
        except Exception as e:
            print(f"Processing error: {e}")

def text_to_speech_thread():
    """خيط مخصص لتحويل النص إلى صوت مع إمكانية المقاطعة"""
    while system_state.is_active:
        try:
            response = response_queue.get(timeout=1)
            if response:
                print(f"\n🤖 Response: {response}")
                
                # تحديد حالة التحدث
                system_state.set_speaking(True)
                
                # التحدث (مع إمكانية المقاطعة)
                tts.text_to_speech(response)
                
                # انتهى التحدث
                system_state.set_speaking(False)
                print("✅ Finished speaking\n")
                
        except Empty:
            continue
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            system_state.set_speaking(False)

def status_monitor_thread():
    """مراقبة وعرض حالة النظام"""
    while system_state.is_active:
        try:
            time.sleep(30)
            if system_state.get_speaking():
                print("ℹ️ Status: Speaking...")
            elif system_state.should_listen():
                print("ℹ️ Status: Active and listening...")
            else:
                print("ℹ️ Status: Paused - say 'hello' to resume")
        except Exception as e:
            print(f"Monitor error: {e}")

def main():
    """الدالة الرئيسية مع إدارة ذكية للحالة والمقاطعة"""
    pygame.init()
    
    print("=" * 60)
    print("🚀 AI Assistant System Starting...")
    print("=" * 60)
    print("\n📋 Available Local Commands (No API needed):")
    print("  • Greetings: 'hello', 'hi', 'مرحبا', 'هلا'")
    print("  • Pause: 'bye', 'goodbye', 'مع السلامة', 'sleep mode'")
    print("  • Resume: 'wake up', 'استيقظ', 'are you there'")
    print("  • Time: 'what time is it', 'كم الساعة'")
    print("  • Date: 'what date is it', 'ما التاريخ'")
    print("  • Thanks: 'thank you', 'شكرا'")
    print("  • Help: 'help', 'مساعدة'")
    print("  • Exit: Press Ctrl+C")
    print("\n🎯 NEW FEATURE: Interrupt Handling")
    print("  • You can interrupt the assistant anytime while it's speaking")
    print("  • Just start speaking and it will stop immediately")
    print("  • All pending processes will be cancelled")
    print("=" * 60)
    
    tts.text_to_speech("Hello, I'm ready to help you.")
    #tts.text_to_speech("Hello, I'm ready to help you. You can interrupt me anytime by just speaking.")
    
    # إنشاء وبدء الخيوط
    threads = [
        #threading.Thread(target=tracker.trackUserFace, name="FaceTracker", args=(False,)),
        #threading.Thread(target=tracker.naturalEyeMovement, name="naturalEyeMovement", args=(False,)),
        threading.Thread(target=eye.playEyeVideo, name="playEyeVideo"),
        threading.Thread(target=audio_recording_thread, daemon=True, name="AudioRecorder"),
        threading.Thread(target=speech_to_text_thread, daemon=True, name="SpeechToText"),
        threading.Thread(target=ai_processing_thread, daemon=True, name="AIProcessor"),
        threading.Thread(target=text_to_speech_thread, daemon=True, name="TextToSpeech"),
        threading.Thread(target=status_monitor_thread, daemon=True, name="StatusMonitor")
    ]
    
    for thread in threads:
        thread.start()
        print(f"✅ Started: {thread.name}")
    
    print("\n" + "=" * 60)
    print("✅ System ready! Start speaking...")
    print("💡 Tip: You can interrupt anytime by speaking while I'm talking")
    print("=" * 60 + "\n")
    
    # إبقاء الخيط الرئيسي حيًا
    try:
        while system_state.is_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⛔ Shutting down system...")
        system_state.stop_system()
        tts.stop_speech() 
        tracker.closeAllWindows()
        print("✅ System stopped successfully")
        print("=" * 60)

if __name__ == "__main__":
    main()