# ==================== AI Assistant System ====================
# Multi-threaded voice assistant with interruption support
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from  ai_n8n import  N8nClient
import pygame
import threading
from queue import Queue, Empty
import time
from local_commands import handle_local_command
import eye_runner as eye
import eye_runner_zero  as eyeZero
# import face_tracker as tracker
# import video_eye_player as eye
import os
import re

# ------------------- Environment Setup -------------------
os.environ.setdefault("DISPLAY", ":0")
os.environ.setdefault("XAUTHORITY", "/home/pi/.Xauthority")
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# ------------------- Initialize Components -------------------
recorder = AudioRecorder()
stt = SpeechToText()
tts = TextToSpeech()
n8n = N8nClient()

# ------------------- Queues for Thread Communication -------------------
audio_queue = Queue()
text_queue = Queue()
response_queue = Queue()

from Config import Config
config = Config()
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
        # Clear audio_queue
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except Empty:
                break
        
        # Clear text_queue
        while not text_queue.empty():
            try:
                text_queue.get_nowait()
            except Empty:
                break
        
        # Clear response_queue
        while not response_queue.empty():
            try:
                response_queue.get_nowait()
            except Empty:
                break


# Initialize system state
system_state = SystemState()

allow_interruption = config.ALLOW_INTERRUPTION or False 

# --- Arabic normalization helpers ---
_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def _normalize_ar(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = _AR_DIACRITICS.sub('', text)     # remove diacritics
    text = text.replace('ـ', '')            # remove tatweel
    # unify alef/hamza variations
    for src in 'أإآٱ':
        text = text.replace(src, 'ا')
    text = text.replace('ة', 'ه')           # optional (helps "خلاصه" vs "خلاص")
    return text

# --- Stop words/phrases (start-of-message) ---
STOP_TOKENS = [
    # English
    "stop","end","cancel","enough","quit","exit","abort","halt",
    # Arabic MSA + dialects
    "قف","توقف","وقف","بس","خلص","خلاص","كفايه","كفاية","ستوب","باركا",  # مغربي: باركا
]

# precompile: start-of-line + token + boundary (space/end/any non-letter/number)
_BOUNDARY = r'(?:\s|$|[^\w\u0600-\u06FF])'
STOP_RE = re.compile(r'^\s*(?:' + '|'.join(map(re.escape, STOP_TOKENS)) + r')' + _BOUNDARY, re.IGNORECASE)

def is_stop_command(text: str) -> bool:
    # check raw (for English), then normalized (for Arabic variants)
    if STOP_RE.search(text or ''):
        return True
    return STOP_RE.search(_normalize_ar(text or '')) is not None

# ================= Worker Threads =================

def audio_recording_thread():
    """
    Thread dedicated to recording audio with interruption detection
    Continuously records audio and puts it in the queue
    """
    while system_state.is_active:
        try:
             
            print(f"system_state.is_speaking: {system_state.is_speaking}")
            print(f"allow_interruption: {allow_interruption}")
            if system_state.is_speaking and  not allow_interruption:
                continue

            # Continuous recording
            audio_buffer = recorder.record_until_silence(
                silence_threshold=500,
                silence_duration=1.5,
                max_duration=20
            )
            
            # Optional: Detect interruption during speaking
            # Uncomment if you want to detect interruption during recording
            '''
            if system_state.get_speaking():
                print("\n🔴 INTERRUPT DETECTED!")
                system_state.interrupt()
            '''
            
            audio_queue.put(audio_buffer)
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            time.sleep(1)


def speech_to_text_thread():
    """
    Thread dedicated to converting speech to text
    Processes audio from queue and converts to text
    """
    while system_state.is_active:
        try:
            audio_buffer = audio_queue.get(timeout=1)
            user_input = stt.transcribe_bytes(audio_buffer)
            print(f"\n🎤 User: {user_input}")
            
            if not system_state.is_speaking:
                    text_queue.put(user_input)

            elif allow_interruption and user_input:
                if is_stop_command(user_input):
                    # Interrupt any ongoing processes
                    system_state.interrupt()
                    text_queue.put(user_input)
                
        except Empty:
            continue
        except Exception as e:
            print(f"❌ Conversion error: {e}")


def ai_processing_thread():
    """
    Thread dedicated to AI processing
    Handles local commands and AI responses
    """
    while system_state.is_active:
        try:
            user_input = text_queue.get(timeout=1)
            
            # Check local commands first
            should_continue, local_response, action, _ = handle_local_command(user_input)
            print(f"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            
            # Handle state changes
            if action == 'pause':
                system_state.pause_listening()
                print("💤 System paused - waiting for wake up command...")
            elif action == 'resume':
                system_state.resume_listening()
                print("✅ System resumed - ready to help!")
            
            # Send response
            if local_response:
                print(F"local_response : {local_response}")
                response_queue.put(local_response)
            
            if should_continue and system_state.should_listen():
                print("🤔 Processing with AI...")
                response = n8n.chat("123456",user_input)
                response_queue.put(response)
                print(response)
            
        except Empty:
            continue
        except Exception as e:
            print(f"❌ Processing error: {e}")


def text_to_speech_thread():
    """
    Thread dedicated to converting text to speech with interruption support
    Plays responses and handles interruptions
    """
    while system_state.is_active:
        try:
            response = response_queue.get(timeout=1)
            if response:
                print(f"\n🤖 Response: {response}")
                
                # Set speaking state
                system_state.set_speaking(True)
                
                # Speak (with possible interruption)
                tts.say(response)
                
                # Finished speaking
                system_state.set_speaking(False)
                print("✅ Finished speaking\n")
                
        except Empty:
            continue
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
            system_state.set_speaking(False)


def status_monitor_thread():
    """
    Monitor and display system status periodically
    """
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
            print(f"❌ Monitor error: {e}")


# ================= Main Function =================

def main():
    """
    Main function with intelligent state and interruption management
    """
    pygame.init()
    
    # Print startup banner
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
    
    # Welcome message
    tts.say("Hello, I'm ready to help you.")
    
    # Create and start threads
    threads = [
        # Uncomment these if you have face tracking and eye video modules
        # threading.Thread(target=tracker.trackUserFace, name="FaceTracker", args=(False,)),
        # threading.Thread(target=tracker.naturalEyeMovement, name="naturalEyeMovement", args=(False,)),
        # threading.Thread(target=eye.playEyeVideo, name="playEyeVideo"),
        # threading.Thread(target=eye.run, name="eye"),
        threading.Thread(target=eyeZero.run, name="eye"),
        threading.Thread(target=audio_recording_thread, daemon=True, name="AudioRecorder"),
        threading.Thread(target=speech_to_text_thread, daemon=True, name="SpeechToText"),
        threading.Thread(target=ai_processing_thread, daemon=True, name="AIProcessor"),
        threading.Thread(target=text_to_speech_thread, daemon=True, name="TextToSpeech"),
        threading.Thread(target=status_monitor_thread, daemon=True, name="StatusMonitor")
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
        print(f"✅ Started: {thread.name}")
    
    print("\n" + "=" * 60)
    print("✅ System ready! Start speaking...")
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
        
        # Cleanup TTS
        try:
            tts.interrupt()
            tts.cleanup()
        except Exception:
            pass

        # Cleanup STT
        try:
            stt.cleanup()
        except Exception:
            pass
        
        # Cleanup face tracker (if enabled)
        # tracker.closeAllWindows()
        
        print("✅ System stopped successfully")
        print("=" * 60)


# ================= Entry Point =================

if __name__ == "__main__":
    main()