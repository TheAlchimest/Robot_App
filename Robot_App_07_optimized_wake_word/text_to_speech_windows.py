# text_to_speech_windows.py - Optimized for Raspberry Pi
# - Uses MP3 format for faster network transfer
# - Streaming playback: starts playing while downloading
# - Lower quality settings for better performance
# - Memory efficient chunk processing

import time
import threading
import queue
import numpy as np
import sounddevice as sd
from elevenlabs.client import ElevenLabs

import io

from Config import Config

VOICE_IDS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "adam": "pNInz6obpgDQGcFmaJgB",
}

class TextToSpeech:
    """
    Even faster version using PCM directly (no MP3 encoding/decoding overhead)
    Best for low-latency on Raspberry Pi
    """
    def __init__(self, config: Config = None):
        self.cfg = config or Config()
        self._interrupt_flag = threading.Event()
        self._playback_lock = threading.Lock()
        self._elevenlabs = ElevenLabs(api_key=self.cfg.ELEVENLABS_API_KEY)
        self.rate = 16000
        self.dtype = "int16"

    def interrupt(self):
        self._interrupt_flag.set()
        try:
            sd.stop()
        except Exception:
            pass

    def reset_interrupt(self):
        self._interrupt_flag.clear()

    def say(self, text: str, voice: str = None) -> bool:
        if not text or not text.strip():
            return False

        voice_name = voice or self.cfg.DEFAULT_VOICE
        voice_id = self.cfg.VOICE_IDS.get(voice_name.lower(), self.cfg.VOICE_IDS.get("adam"))
        
        if not voice_id:
            print(f"[TTS] ❌ No valid voice ID found")
            return False
        
        with self._playback_lock:
            self.reset_interrupt()
            
            try:
                start = time.time()
                
                # Use lowest quality PCM for fastest transfer
                audio_chunks = self._elevenlabs.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id="eleven_turbo_v2_5",
                    output_format="pcm_16000",  # Raw PCM, no encoding overhead
                )
                
                # Collect chunks
                pcm_data = b""
                for chunk in audio_chunks:
                    if self._interrupt_flag.is_set():
                        return False
                    pcm_data += chunk
                
                elapsed = time.time() - start
                print(f"[TTS] ✅ Ready in {elapsed:.2f}s")
                
                if self._interrupt_flag.is_set():
                    return False
                
                # Play directly
                arr = np.frombuffer(pcm_data, dtype=self.dtype)
                sd.play(arr, samplerate=self.rate, blocking=False)
                
                while sd.get_stream() is not None and sd.get_stream().active:
                    if self._interrupt_flag.is_set():
                        sd.stop()
                        return False
                    time.sleep(0.05)
                
                return True
                
            except Exception as e:
                print(f"[TTS] ❌ Error: {e}")
                return False

    def cleanup(self):
        self.interrupt()


if __name__ == "__main__":
    from Config import Config
    
    cfg = Config()
    
    # Test both versions
    print("\n=== Testing Standard Version ===")
    tts = TextToSpeech(cfg)
    success = tts.say("Testing standard version with MP3")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    tts.cleanup()
    
    print("\n=== Testing Fast Version (Recommended for Pi) ===")
    tts_fast = TextToSpeechFast(cfg)
    success = tts_fast.say("Testing fast version with PCM")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    tts_fast.cleanup()