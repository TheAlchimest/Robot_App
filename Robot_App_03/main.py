# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
import text_to_speech as tts
import ai_model as llm
import pygame
import threading
from queue import Queue
import time
from local_commands import handle_local_command

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

system_state = SystemState()

def audio_recording_thread():
    """Dedicated thread for audio recording"""
    while system_state.is_active:
        try:
            # Always record audio, but processing depends on state
            audio_buffer = recorder.record_until_silence(
                silence_threshold=500,
                silence_duration=1.5,
                max_duration=20
            )
            audio_queue.put(audio_buffer)
        except Exception as e:
            print(f"Recording error: {e}")
            time.sleep(1)  # Brief pause before retrying

def speech_to_text_thread():
    """Dedicated thread for speech to text conversion"""
    while system_state.is_active:
        try:
            audio_buffer = audio_queue.get()
            user_input = stt.convert(audio_buffer)
            
            if user_input:
                print(f"📝 User: {user_input}")
                text_queue.put(user_input)
        except Exception as e:
            print(f"Conversion error: {e}")

def ai_processing_thread():
    """Dedicated thread for AI processing with local command handling"""
    while system_state.is_active:
        try:
            user_input = text_queue.get()
            
            # Check local commands first
            should_continue, local_response, action = handle_local_command(user_input)
            
            # Handle state changes
            if action == 'pause':
                system_state.pause_listening()
                print("💤 System paused - waiting for wake up command...")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ System resumed - ready to help!")
            
            # Send response
            if local_response:
                response_queue.put(local_response)
            elif should_continue and system_state.should_listen():
                # Only call API if system is listening
                response = llm.chat(user_input)
                response_queue.put(response)
            
        except Exception as e:
            print(f"Processing error: {e}")

def text_to_speech_thread():
    """Dedicated thread for text to speech conversion"""
    while system_state.is_active:
        try:
            response = response_queue.get()
            if response:  # Only speak if there's a response
                print(f"🤖 Response: {response}")
                tts.text_to_speech(response)
        except Exception as e:
            print(f"Text-to-speech error: {e}")

def status_monitor_thread():
    """Monitor and display system status periodically"""
    while system_state.is_active:
        try:
            time.sleep(30)  # Check every 30 seconds
            if system_state.should_listen():
                print("ℹ️ Status: Active and listening...")
            else:
                print("ℹ️ Status: Paused - say 'hello' to resume")
        except Exception as e:
            print(f"Monitor error: {e}")

def main():
    """Main function with smart state management"""
    pygame.init()
    
    print("=" * 50)
    print("🚀 AI Assistant System Starting...")
    print("=" * 50)
    print("\n📋 Available Local Commands (No API needed):")
    print("  • Greetings: 'hello', 'hi', 'مرحبا', 'هلا'")
    print("  • Pause: 'bye', 'goodbye', 'مع السلامة', 'sleep mode'")
    print("  • Resume: 'wake up', 'استيقظ', 'are you there'")
    print("  • Time: 'what time is it', 'كم الساعة'")
    print("  • Date: 'what date is it', 'ما التاريخ'")
    print("  • Thanks: 'thank you', 'شكرا'")
    print("  • Help: 'help', 'مساعدة'")
    print("  • Exit: Press Ctrl+C")
    print("=" * 50)
    
    tts.text_to_speech("Hello, I'm ready to help you. You can pause me anytime by saying goodbye.")
    
    # Create and start threads
    threads = [
        threading.Thread(target=audio_recording_thread, daemon=True, name="AudioRecorder"),
        threading.Thread(target=speech_to_text_thread, daemon=True, name="SpeechToText"),
        threading.Thread(target=ai_processing_thread, daemon=True, name="AIProcessor"),
        threading.Thread(target=text_to_speech_thread, daemon=True, name="TextToSpeech"),
        threading.Thread(target=status_monitor_thread, daemon=True, name="StatusMonitor")
    ]
    
    for thread in threads:
        thread.start()
        print(f"✅ Started: {thread.name}")
    
    print("\n" + "=" * 50)
    print("✅ System ready! Start speaking...")
    print("=" * 50 + "\n")
    
    # Keep main thread alive
    try:
        while system_state.is_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("⛔ Shutting down system...")
        system_state.stop_system()
        print("✅ System stopped successfully")
        print("=" * 50)

if __name__ == "__main__":
    main()