# text_to_speech.py
# تحسينات: Streaming playback، interrupt محسّن، connection pooling

import io
import time
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Config import Config

# Try different audio backends
try:
    import pyalsaaudio
    _HAS_ALSA = True
except ImportError:
    _HAS_ALSA = False

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False

class TextToSpeech:
    def __init__(self, config: Config = None):
        self.cfg = config or Config()
        self.api_key = self.cfg.ELEVENLABS_API_KEY
        
        if not self.api_key:
            raise ValueError("Missing ELEVENLABS_API_KEY")

        self.url_base = "https://api.elevenlabs.io/v1/text-to-speech"
        
        # ✅ Session مع connection pooling
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=2,
            pool_maxsize=5
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.session.headers.update({
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        })

        # ✅ Interrupt flag
        self._interrupt_flag = threading.Event()
        self._playback_lock = threading.Lock()
        
        # تحديد الـ audio backend
        self._init_audio_backend()

    def _init_audio_backend(self):
        """تهيئة audio backend حسب المتاح"""
        backend = self.cfg.AUDIO_BACKEND
        
        if backend == "alsa" and _HAS_ALSA:
            self.backend = "alsa"
            print("[TTS] Using ALSA backend")
        elif backend == "pygame" and _HAS_PYGAME:
            self.backend = "pygame"
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            print("[TTS] Using pygame backend")
        elif backend == "aplay" or not backend:
            self.backend = "aplay"
            print("[TTS] Using aplay backend")
        else:
            # Auto-detect
            if _HAS_ALSA:
                self.backend = "alsa"
                print("[TTS] Auto-detected ALSA")
            elif _HAS_PYGAME:
                self.backend = "pygame"
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                print("[TTS] Auto-detected pygame")
            else:
                self.backend = "aplay"
                print("[TTS] Fallback to aplay")

    def interrupt(self):
        """قطع التشغيل الحالي"""
        self._interrupt_flag.set()
        
        # Stop playback based on backend
        try:
            if self.backend == "pygame" and _HAS_PYGAME:
                pygame.mixer.music.stop()
            elif self.backend == "alsa" and hasattr(self, '_alsa_device'):
                if self._alsa_device:
                    self._alsa_device.pause()
        except Exception:
            pass

    def reset_interrupt(self):
        """إعادة تعيين interrupt flag"""
        self._interrupt_flag.clear()

    def say(self, text: str, voice: str = None) -> bool:
        """
        تحويل النص لصوت وتشغيله
        
        Args:
            text: النص المراد تحويله
            voice: اسم الصوت (افتراضي من Config)
            
        Returns:
            True إذا نجح، False إذا فشل أو تم المقاطعة
        """
        if not text or not text.strip():
            return False

        voice = voice or self.cfg.DEFAULT_VOICE
        voice_id = self.cfg.VOICE_IDS.get(voice.lower(), voice)

        with self._playback_lock:
            self.reset_interrupt()
            
            # ✅ Get audio from ElevenLabs
            audio_data = self._fetch_audio(text, voice_id)
            
            if not audio_data:
                return False
            
            if self._interrupt_flag.is_set():
                return False
            
            # ✅ Play audio
            return self._play_audio(audio_data)

    def _fetch_audio(self, text: str, voice_id: str) -> bytes:
        """جلب الصوت من ElevenLabs API"""
        url = f"{self.url_base}/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",  # ✅ أسرع موديل
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }

        try:
            start_time = time.time()
            
            resp = self.session.post(
                url,
                json=payload,
                timeout=15,
                stream=True  # ✅ Streaming للسرعة
            )
            
            resp.raise_for_status()
            
            # Read audio data
            audio_data = b""
            for chunk in resp.iter_content(chunk_size=8192):
                if self._interrupt_flag.is_set():
                    return b""
                audio_data += chunk
            
            elapsed = time.time() - start_time
            print(f"[TTS] ✅ Fetched audio in {elapsed:.2f}s ({len(audio_data)} bytes)")
            
            return audio_data

        except requests.RequestException as e:
            print(f"[TTS] ❌ Fetch error: {e}")
            return b""

    def _play_audio(self, audio_data: bytes) -> bool:
        """تشغيل الصوت حسب الـ backend"""
        try:
            if self.backend == "alsa":
                return self._play_alsa(audio_data)
            elif self.backend == "pygame":
                return self._play_pygame(audio_data)
            else:  # aplay
                return self._play_aplay(audio_data)
        except Exception as e:
            print(f"[TTS] ❌ Playback error: {e}")
            return False

    def _play_alsa(self, audio_data: bytes) -> bool:
        """تشغيل باستخدام ALSA"""
        if not _HAS_ALSA:
            return False
        
        try:
            import wave
            
            # Parse WAV to get format
            wav_io = io.BytesIO(audio_data)
            with wave.open(wav_io, 'rb') as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                
                device = pyalsaaudio.PCM(
                    type=pyalsaaudio.PCM_PLAYBACK,
                    device=self.cfg.AUDIO_DEVICE
                )
                device.setchannels(channels)
                device.setrate(rate)
                device.setformat(pyalsaaudio.PCM_FORMAT_S16_LE)
                device.setperiodsize(1024)
                
                self._alsa_device = device
                
                # Play chunks
                pcm_data = wf.readframes(wf.getnframes())
                chunk_size = 4096
                
                for i in range(0, len(pcm_data), chunk_size):
                    if self._interrupt_flag.is_set():
                        device.close()
                        return False
                    
                    chunk = pcm_data[i:i + chunk_size]
                    device.write(chunk)
                
                device.close()
                self._alsa_device = None
                return True
                
        except Exception as e:
            print(f"[TTS] ALSA error: {e}")
            return False

    def _play_pygame(self, audio_data: bytes) -> bool:
        """تشغيل باستخدام pygame"""
        if not _HAS_PYGAME:
            return False
        
        try:
            sound_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(sound_io)
            pygame.mixer.music.play()
            
            # انتظار انتهاء التشغيل
            while pygame.mixer.music.get_busy():
                if self._interrupt_flag.is_set():
                    pygame.mixer.music.stop()
                    return False
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"[TTS] pygame error: {e}")
            return False

    def _play_aplay(self, audio_data: bytes) -> bool:
        """تشغيل باستخدام aplay"""
        import subprocess
        import tempfile
        import os
        
        try:
            # حفظ مؤقت للملف
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # تشغيل
            process = subprocess.Popen(
                ["aplay", "-q", tmp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # انتظار مع إمكانية المقاطعة
            while process.poll() is None:
                if self._interrupt_flag.is_set():
                    process.terminate()
                    process.wait(timeout=1)
                    os.unlink(tmp_path)
                    return False
                time.sleep(0.1)
            
            os.unlink(tmp_path)
            return True
            
        except Exception as e:
            print(f"[TTS] aplay error: {e}")
            return False

    def cleanup(self):
        """تنظيف الموارد"""
        try:
            self.session.close()
        except Exception:
            pass
        
        try:
            if self.backend == "pygame" and _HAS_PYGAME:
                pygame.mixer.quit()
        except Exception:
            pass
