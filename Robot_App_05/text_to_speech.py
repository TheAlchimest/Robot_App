import os
import tempfile
import pygame
import threading
from elevenlabs.client import ElevenLabs
from Config import Config

config = Config()
elevenlabs = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

# Initialize pygame once
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# Available voices
VOICE_IDS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "adam": "pNInz6obpgDQGcFmaJgB",
}

# Global state for interrupt handling
class TTSState:
    def __init__(self):
        self.is_playing = False
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        self.current_temp_file = None
    
    def set_playing(self, playing):
        with self.lock:
            self.is_playing = playing
    
    def get_playing(self):
        with self.lock:
            return self.is_playing
    
    def signal_stop(self):
        self.stop_flag.set()
    
    def clear_stop(self):
        self.stop_flag.clear()
    
    def should_stop(self):
        return self.stop_flag.is_set()
    
    def set_temp_file(self, path):
        with self.lock:
            self.current_temp_file = path
    
    def cleanup_temp_file(self):
        with self.lock:
            if self.current_temp_file:
                try:
                    os.remove(self.current_temp_file)
                except:
                    pass
                self.current_temp_file = None

tts_state = TTSState()

def text_to_speech(text: str, voice: str = "adam") -> None:
    """
    Optimized text to speech conversion with interrupt capability
    
    Args:
        text: Text to convert to speech
        voice: Voice ID to use (default: adam)
    """
    if not text:
        return
    
    # Clear stop flag for new speech
    tts_state.clear_stop()
    tts_state.set_playing(True)
    
    tmp_path = None
    
    try:
        # Use MP3 for speed
        audio_chunks = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=VOICE_IDS.get(voice, VOICE_IDS["adam"]),
            model_id="eleven_turbo_v2_5",  # Fastest model
            output_format="mp3_44100_128",
        )
        
        # Check for interrupt during generation
        if tts_state.should_stop():
            print("🛑 Speech generation cancelled")
            tts_state.set_playing(False)
            return
        
        # Collect chunks
        audio_bytes = b"".join(chunk for chunk in audio_chunks)
        
        # Check for interrupt after generation
        if tts_state.should_stop():
            print("🛑 Speech cancelled before playback")
            tts_state.set_playing(False)
            return
        
        # Direct playback
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_bytes)
            tmp_path = f.name
        
        tts_state.set_temp_file(tmp_path)
        
        # Fast playback with interrupt checking
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        # Efficient waiting with interrupt checking
        while pygame.mixer.music.get_busy():
            # Check for interrupt every 10ms
            if tts_state.should_stop():
                pygame.mixer.music.stop()
                print("🛑 Speech interrupted during playback")
                break
            pygame.time.wait(10)
        
    except Exception as e:
        print(f"❌ TTS error: {e}")
    
    finally:
        # Cleanup
        tts_state.set_playing(False)
        if tmp_path:
            try:
                os.remove(tmp_path)
            except:
                pass
        tts_state.set_temp_file(None)

def stop_speech():
    """
    Stop currently playing speech immediately
    """
    if tts_state.get_playing():
        print("✋ Stopping speech...")
        tts_state.signal_stop()
        
        try:
            pygame.mixer.music.stop()
        except:
            pass
        
        # Cleanup temp file
        tts_state.cleanup_temp_file()
        tts_state.set_playing(False)
        print("✅ Speech stopped")

def is_currently_speaking():
    """
    Check if TTS is currently playing
    
    Returns:
        bool: True if speech is playing, False otherwise
    """
    return tts_state.get_playing()

def text_to_speech_async(text: str, voice: str = "adam"):
    """
    Async version for use with threading
    
    Args:
        text: Text to convert to speech
        voice: Voice ID to use
    
    Returns:
        threading.Thread: The thread running the TTS
    """
    thread = threading.Thread(target=text_to_speech, args=(text, voice))
    thread.daemon = True
    thread.start()
    return thread

if __name__ == "__main__":
    import time
    
    print("🧪 Testing TTS with interrupt capability...")
    print("=" * 50)
    
    # Test 1: Normal speech
    print("\n1️⃣ Test: Normal speech")
    text_to_speech("Hello, this is a test of the text to speech system with interrupt capability.")
    
    time.sleep(1)
    
    # Test 2: Interrupt during speech
    print("\n2️⃣ Test: Interrupt during speech")
    thread = text_to_speech_async("This is a very long message that should be interrupted in the middle. I will keep talking for a while to demonstrate the interrupt functionality working correctly.")
    
    time.sleep(2)  # Let it play for 2 seconds
    print("\n⚠️ Interrupting now...")
    stop_speech()
    
    time.sleep(1)
    
    # Test 3: New speech after interrupt
    print("\n3️⃣ Test: New speech after interrupt")
    text_to_speech("This is a new message after the interrupt. The system should work normally.")
    
    print("\n✅ All tests completed!")
    print("=" * 50)