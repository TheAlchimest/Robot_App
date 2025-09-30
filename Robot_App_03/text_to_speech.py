import os
import tempfile
import pygame
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

def text_to_speech(text: str, voice: str = "adam") -> None:
    """
    Optimized text to speech conversion with no delay
    
    Args:
        text: Text to convert to speech
        voice: Voice ID to use (default: adam)
    """
    if not text:
        return
    
    try:
        # Use MP3 for speed
        audio_chunks = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=VOICE_IDS.get(voice, VOICE_IDS["adam"]),
            model_id="eleven_turbo_v2_5",  # Fastest model
            output_format="mp3_44100_128",
        )
        
        # Collect chunks
        audio_bytes = b"".join(chunk for chunk in audio_chunks)
        
        # Direct playback
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_bytes)
            tmp_path = f.name
        
        # Fast playback
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        # Efficient waiting
        while pygame.mixer.music.get_busy():
            pygame.time.wait(10)
        
        # Cleanup
        try:
            os.remove(tmp_path)
        except:
            pass
            
    except Exception as e:
        print(f"TTS error: {e}")

def text_to_speech_async(text: str, voice: str = "adam"):
    """Async version for use with threading"""
    import threading
    thread = threading.Thread(target=text_to_speech, args=(text, voice))
    thread.daemon = True
    thread.start()
    return thread

if __name__ == "__main__":
    text_to_speech("Hello, how are you?")
