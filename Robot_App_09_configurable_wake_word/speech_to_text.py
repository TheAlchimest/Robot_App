# speech_to_text.py
# تحسينات: إلغاء Disk I/O، استخدام memory buffers، connection pooling

import io
import time
import wave
import subprocess
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Config import Config

DEFAULT_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_STT_MODEL = "eleven_multilingual_v2"

TARGET_RATE = 16000
TARGET_CHANNELS = 1
SAMPLE_WIDTH = 2

class SpeechToText:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.api_key = getattr(self.config, "ELEVENLABS_API_KEY", None)
        if not self.api_key:
            raise ValueError("Missing ELEVENLABS_API_KEY")

        self.url = getattr(self.config, "ELEVEN_STT_URL", DEFAULT_STT_URL)
        self.model = getattr(self.config, "ELEVEN_STT_MODEL", DEFAULT_STT_MODEL)

        # ✅ Connection pooling لتقليل latency
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=5)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def transcribe_bytes(self, audio_bytes: bytes, is_wav: Optional[bool] = None) -> str:
        if not audio_bytes:
            return ""

        # ✅ التحقق من WAV format
        if is_wav is None:
            is_wav = len(audio_bytes) >= 12 and audio_bytes[0:4] == b"RIFF"

        if not is_wav:
            audio_bytes = self._pcm_to_wav_bytes(audio_bytes)

        # ✅ Optional VAD trimming (في الذاكرة)
        audio_bytes = self._trim_silence(audio_bytes)

        # ✅ Upload من memory مباشرة (بدون disk I/O)
        return self._upload_bytes(audio_bytes, "audio/wav")

    def _pcm_to_wav_bytes(self, pcm: bytes) -> bytes:
        """تحويل PCM لـ WAV في الذاكرة"""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(TARGET_CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(TARGET_RATE)
            wf.writeframes(pcm)
        return buf.getvalue()

    def _trim_silence(self, wav_bytes: bytes) -> bytes:
        """قص الصمت باستخدام WebRTC VAD (في الذاكرة)"""
        try:
            import webrtcvad
        except ImportError:
            return wav_bytes

        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                rate = wf.getframerate()
                ch = wf.getnchannels()
                sw = wf.getsampwidth()
                
                if rate != TARGET_RATE or ch != TARGET_CHANNELS or sw != SAMPLE_WIDTH:
                    return wav_bytes
                
                pcm = wf.readframes(wf.getnframes())

            vad = webrtcvad.Vad(2)
            frame_ms = 30
            frame_bytes = int(TARGET_RATE * (frame_ms / 1000.0)) * SAMPLE_WIDTH

            frames = [pcm[i:i + frame_bytes] for i in range(0, len(pcm), frame_bytes)]
            voiced = [vad.is_speech(f, TARGET_RATE) if len(f) == frame_bytes else False 
                     for f in frames]

            if not any(voiced):
                return wav_bytes

            first = next((i for i, v in enumerate(voiced) if v), 0)
            last = len(voiced) - 1 - next((i for i, v in enumerate(reversed(voiced)) if v), 0)

            pad = 2
            start = max(0, (first - pad) * frame_bytes)
            end = min(len(pcm), (last + pad + 1) * frame_bytes)
            trimmed = pcm[start:end]

            return self._pcm_to_wav_bytes(trimmed)
        except Exception:
            return wav_bytes

    def _upload_bytes(self, audio_bytes: bytes, mime: str) -> str:
        """Upload من memory مباشرة باستخدام session pool"""
        headers = {"xi-api-key": self.api_key}
        data = {"model_id": self.model}

        try:
            # ✅ Upload من BytesIO مباشرة (بدون disk I/O)
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), mime)}
            
            resp = self.session.post(
                self.url,
                headers=headers,
                data=data,
                files=files,
                timeout=15  # ✅ timeout أقصر
            )
            resp.raise_for_status()

            try:
                js = resp.json()
            except ValueError:
                return resp.text.strip()

            if isinstance(js, dict):
                text = js.get("text", "") or js.get("transcription", "")
                if text:
                    return text.strip()
                
                if "result" in js and isinstance(js["result"], dict):
                    text = js["result"].get("text", "")
                    if text:
                        return text.strip()

            return str(js).strip() if js else ""

        except requests.RequestException as e:
            print(f"[STT] Upload failed: {e}")
            return ""

    def cleanup(self):
        """Close session"""
        try:
            self.session.close()
        except Exception:
            pass
