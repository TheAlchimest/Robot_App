# speech_to_text.py
# -------------------------------------------------------------------
# High-performance STT client for Raspberry Pi using ElevenLabs API.
# - Prefers FLAC (via ffmpeg) to upload smaller files (faster on weak CPUs).
# - Fallback to WAV 16k mono if ffmpeg not available.
# - Optional VAD (WebRTC) trimming to cut leading/trailing silence & noise.
# - Robust networking: timeout, retries with backoff, strict JSON parsing.
#
# Dependencies:
#   pip install requests
#   Optional (recommended on Pi): sudo apt-get install ffmpeg
#   Optional VAD: pip install webrtcvad
#
# Config.py must provide:
#   ELEVENLABS_API_KEY: str
#   (optional) ELEVEN_STT_URL: str (default: https://api.elevenlabs.io/v1/speech-to-text)
#   (optional) ELEVEN_STT_MODEL: str (default: "eleven_multilingual_v2")
# -------------------------------------------------------------------

import io
import os
import sys
import json
import time
import wave
import uuid
import shutil
import tempfile
import subprocess
from typing import Optional, Tuple

import requests

from Config import Config  # expects ELEVENLABS_API_KEY, optional ELEVEN_STT_URL, ELEVEN_STT_MODEL


# ------------------------------ Defaults ------------------------------

DEFAULT_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_STT_MODEL = "eleven_multilingual_v2"

HTTP_TIMEOUT = 30          # seconds
MAX_RETRIES = 3
BACKOFF_BASE = 0.5         # seconds

TARGET_RATE = 16000
TARGET_CHANNELS = 1
SAMPLE_WIDTH = 2           # 16-bit PCM


# ---------------------------- Small Utilities ----------------------------

def _cmd_exists(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None


def _wav_info(data: bytes) -> Tuple[bool, int, int, int]:
    """
    Return (is_wav, sample_rate, channels, sampwidth) for given bytes.
    If not a WAV, return (False, 0, 0, 0).
    """
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(io.BytesIO(data), "rb") as wf:
                return True, wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        except Exception:
            return True, 0, 0, 0
    return False, 0, 0, 0


def _pcm16_to_wav_bytes(pcm: bytes, sample_rate: int = TARGET_RATE, channels: int = TARGET_CHANNELS) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def _save_bytes(tmp_dir: str, data: bytes, suffix: str) -> str:
    f = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=suffix)
    f.write(data)
    f.flush()
    f.close()
    return f.name


def _ffmpeg_wav_to_flac(src_wav: str, dst_flac: str) -> bool:
    """
    Convert WAV to FLAC via ffmpeg (if available). Returns True on success.
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "error",
            "-i", src_wav,
            "-ac", str(TARGET_CHANNELS),
            "-ar", str(TARGET_RATE),
            "-sample_fmt", "s16",
            dst_flac
        ]
        subprocess.run(cmd, check=True)
        return os.path.isfile(dst_flac) and os.path.getsize(dst_flac) > 0
    except Exception:
        return False


# ---------------------------- Optional VAD (WebRTC) ----------------------------

def _trim_with_vad_if_available(wav_bytes: bytes) -> bytes:
    """
    If webrtcvad is installed, trim leading/trailing silence to reduce upload size.
    Returns wav_bytes unchanged if VAD not available or any error occurs.
    """
    try:
        import webrtcvad
    except ImportError:
        return wav_bytes

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            rate = wf.getframerate()
            ch = wf.getnchannels()
            sw = wf.getsampwidth()
            assert rate == TARGET_RATE and ch == TARGET_CHANNELS and sw == SAMPLE_WIDTH, \
                "VAD trimming expects 16k mono 16-bit WAV"
            pcm = wf.readframes(wf.getnframes())

        vad = webrtcvad.Vad(2)  # 0-3
        frame_ms = 30           # 10/20/30 ms only
        frame_bytes = int(TARGET_RATE * (frame_ms / 1000.0)) * SAMPLE_WIDTH

        frames = [pcm[i:i + frame_bytes] for i in range(0, len(pcm), frame_bytes)]
        voiced = [vad.is_speech(f, TARGET_RATE) if len(f) == frame_bytes else False for f in frames]

        if not any(voiced):
            return wav_bytes

        first = next((i for i, v in enumerate(voiced) if v), 0)
        last = len(voiced) - 1 - next((i for i, v in enumerate(reversed(voiced)) if v), 0)

        pad = 2  # ~60 ms
        start = max(0, (first - pad) * frame_bytes)
        end = min(len(pcm), (last + pad + 1) * frame_bytes)
        trimmed = pcm[start:end]

        return _pcm16_to_wav_bytes(trimmed, TARGET_RATE, TARGET_CHANNELS)
    except Exception:
        return wav_bytes


# ---------------------------- STT Core Client ----------------------------

class SpeechToText:
    """
    ElevenLabs Speech-to-Text client optimized for Raspberry Pi.
    Use transcribe_bytes() if you already have audio in memory (WAV/PCM16 @16k mono).
    Use transcribe_file() to read a file and transcribe.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.api_key = getattr(self.config, "ELEVENLABS_API_KEY", None)
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is missing. Please set it in your environment/Config.py")

        self.url = getattr(self.config, "ELEVEN_STT_URL", DEFAULT_STT_URL)
        self.model = getattr(self.config, "ELEVEN_STT_MODEL", DEFAULT_STT_MODEL)

        self._can_ffmpeg = _cmd_exists("ffmpeg")
        self._tmp_dir = tempfile.mkdtemp(prefix="stt_tmp_")

    def transcribe_bytes(self, audio_bytes: bytes, is_wav: Optional[bool] = None) -> str:
        if not audio_bytes:
            return ""

        if is_wav is None:
            is_wav, rate, ch, sw = _wav_info(audio_bytes)
        else:
            rate = TARGET_RATE
            ch = TARGET_CHANNELS
            sw = SAMPLE_WIDTH

        if not is_wav:
            audio_bytes = _pcm16_to_wav_bytes(audio_bytes, TARGET_RATE, TARGET_CHANNELS)
            is_wav, rate, ch, sw = True, TARGET_RATE, TARGET_CHANNELS, SAMPLE_WIDTH

        # Optional VAD trimming
        audio_bytes = _trim_with_vad_if_available(audio_bytes)

        wav_path = _save_bytes(self._tmp_dir, audio_bytes, suffix=".wav")

        flac_path = None
        if self._can_ffmpeg:
            flac_path = os.path.join(self._tmp_dir, f"{uuid.uuid4().hex}.flac")
            if not _ffmpeg_wav_to_flac(wav_path, flac_path):
                flac_path = None

        try:
            if flac_path:
                return self._upload_file(flac_path, "audio/flac")
            else:
                return self._upload_file(wav_path, "audio/wav")
        finally:
            try:
                if flac_path and os.path.exists(flac_path): os.remove(flac_path)
            except Exception: pass
            try:
                if os.path.exists(wav_path): os.remove(wav_path)
            except Exception: pass

    def transcribe_file(self, path: str) -> str:
        if not path or not os.path.isfile(path):
            return ""
        ext = os.path.splitext(path)[1].lower()

        mime = "audio/wav"
        if ext == ".flac":
            mime = "audio/flac"
        elif ext in (".mp3", ".m4a", ".ogg", ".opus"):
            if self._can_ffmpeg:
                flac_path = os.path.join(self._tmp_dir, f"{uuid.uuid4().hex}.flac")
                try:
                    if _ffmpeg_wav_to_flac(path, flac_path):
                        return self._upload_file(flac_path, "audio/flac")
                finally:
                    try: os.remove(flac_path)
                    except: pass
            mime = "audio/mpeg" if ext == ".mp3" else "application/octet-stream"

        return self._upload_file(path, mime)

    def cleanup(self):
        try:
            if os.path.isdir(self._tmp_dir):
                shutil.rmtree(self._tmp_dir, ignore_errors=True)
        except Exception:
            pass

    def _upload_file(self, file_path: str, mime: str) -> str:
        headers = {"xi-api-key": self.api_key}
        data = {"model_id": self.model}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with open(file_path, "rb") as f:
                    files = {"file": (os.path.basename(file_path), f, mime)}
                    resp = requests.post(
                        self.url, headers=headers, data=data, files=files,
                        timeout=HTTP_TIMEOUT
                    )
                resp.raise_for_status()

                try:
                    js = resp.json()
                except ValueError:
                    return resp.text.strip()

                if isinstance(js, dict):
                    if "text" in js and isinstance(js["text"], str):
                        return js["text"].strip()
                    if "transcription" in js and isinstance(js["transcription"], str):
                        return js["transcription"].strip()
                    if "result" in js and isinstance(js["result"], dict):
                        t = js["result"].get("text", "")
                        if isinstance(t, str): return t.strip()
                return (js if isinstance(js, str) else json.dumps(js, ensure_ascii=False)).strip()

            except requests.RequestException as e:
                if attempt == MAX_RETRIES:
                    print(f"[STT] Upload failed (final): {e}")
                    return ""
                time.sleep(BACKOFF_BASE * attempt)
            except Exception as e:
                print(f"[STT] Unexpected error: {e}")
                return ""

        return ""

if __name__ == "__main__":
    cfg = Config()
    stt = SpeechToText(cfg)

    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    if test_path and os.path.isfile(test_path):
        print("Transcription:", stt.transcribe_file(test_path))
    else:
        # tiny silence test
        samples = b"\x00\x00" * TARGET_RATE
        wav_bytes = _pcm16_to_wav_bytes(samples, TARGET_RATE, 1)
        print("Transcription:", stt.transcribe_bytes(wav_bytes, is_wav=True))

    stt.cleanup()
