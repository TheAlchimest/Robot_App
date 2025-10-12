import io
import os
import wave
import uuid
import shutil
import tempfile
import subprocess
from typing import Optional, Tuple
from io import BytesIO

import numpy as np
import sounddevice as sd
from elevenlabs import ElevenLabs

from Config import Config

TARGET_RATE = 16000
TARGET_CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM

def _cmd_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    from shutil import which
    return which(cmd) is not None

def _wav_info(data: bytes) -> Tuple[bool, int, int, int]:
    """Extract WAV file information"""
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(io.BytesIO(data), "rb") as wf:
                return True, wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        except Exception:
            return True, 0, 0, 0
    return False, 0, 0, 0

def _pcm16_to_wav_bytes(pcm: bytes, sample_rate: int = TARGET_RATE, channels: int = TARGET_CHANNELS) -> bytes:
    """Convert raw PCM16 to WAV format"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def _save_bytes(tmp_dir: str, data: bytes, suffix: str) -> str:
    """Save bytes to a temporary file"""
    f = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix=suffix)
    f.write(data)
    f.flush()
    f.close()
    return f.name

def _ffmpeg_convert(src_path: str, dst_path: str) -> bool:
    """Convert audio file to WAV using ffmpeg"""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "error",
            "-i", src_path,
            "-ac", str(TARGET_CHANNELS),
            "-ar", str(TARGET_RATE),
            "-sample_fmt", "s16",
            dst_path
        ]
        subprocess.run(cmd, check=True)
        return os.path.isfile(dst_path) and os.path.getsize(dst_path) > 0
    except Exception:
        return False

# ---------------------------- Unified recording via sounddevice ----------------------------
def record_via_sounddevice(seconds: float) -> bytes:
    """
    Records audio at 16k/mono/int16 using sounddevice and returns WAV bytes.
    """
    rec = sd.rec(int(seconds * TARGET_RATE), samplerate=TARGET_RATE, channels=TARGET_CHANNELS, dtype="int16")
    sd.wait()
    return _pcm16_to_wav_bytes(rec.tobytes(order="C"), TARGET_RATE, TARGET_CHANNELS)

# ---------------------------- Optional VAD (WebRTC) ----------------------------
def _trim_with_vad_if_available(wav_bytes: bytes) -> bytes:
    """Trim silence from audio using WebRTC VAD if available"""
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

        vad = webrtcvad.Vad(2)
        frame_ms = 30
        frame_bytes = int(TARGET_RATE * (frame_ms / 1000.0)) * SAMPLE_WIDTH

        frames = [pcm[i:i + frame_bytes] for i in range(0, len(pcm), frame_bytes)]
        voiced = [False if len(f) != frame_bytes else vad.is_speech(f, TARGET_RATE) for f in frames]
        if not any(voiced):
            return wav_bytes

        first = next((i for i, v in enumerate(voiced) if v), 0)
        last = len(voiced) - 1 - next((i for i, v in enumerate(reversed(voiced)) if v), 0)
        pad = 2
        start = max(0, (first - pad) * frame_bytes)
        end = min(len(pcm), (last + pad + 1) * frame_bytes)
        trimmed = pcm[start:end]
        return _pcm16_to_wav_bytes(trimmed, TARGET_RATE, TARGET_CHANNELS)
    except Exception:
        return wav_bytes

class SpeechToText:
    """
    Speech-to-Text class using ElevenLabs API
    """
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.api_key = getattr(self.config, "ELEVENLABS_API_KEY", None)
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is missing. Please set it in your environment/Config.py")

        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=self.api_key)
        
        # Model settings
        self.model = getattr(self.config, "ELEVEN_STT_MODEL", "scribe_v1")
        self.language_code = getattr(self.config, "ELEVEN_STT_LANGUAGE", None)  # None = auto-detect
        self.enable_diarize = getattr(self.config, "ELEVEN_STT_DIARIZE", False)
        self.enable_audio_events = getattr(self.config, "ELEVEN_STT_AUDIO_EVENTS", False)

        self._can_ffmpeg = _cmd_exists("ffmpeg")
        self._tmp_dir = tempfile.mkdtemp(prefix="stt_tmp_")

    def transcribe_bytes(self, audio_bytes: bytes, is_wav: Optional[bool] = None) -> str:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Raw audio data
            is_wav: Whether the data is in WAV format (None = auto-detect)
            
        Returns:
            Transcribed text
        """
        if not audio_bytes:
            return ""

        # Check minimum audio length
        if len(audio_bytes) < 1000:
            print("[STT] ⚠️ Audio too short, skipping transcription")
            return ""

        if is_wav is None:
            is_wav, rate, ch, sw = _wav_info(audio_bytes)
        else:
            rate = TARGET_RATE
            ch = TARGET_CHANNELS
            sw = SAMPLE_WIDTH

        if not is_wav:
            audio_bytes = _pcm16_to_wav_bytes(audio_bytes, TARGET_RATE, TARGET_CHANNELS)
            is_wav = True

        # Apply VAD trimming
        audio_bytes = _trim_with_vad_if_available(audio_bytes)
        
        # Check again after trimming
        if len(audio_bytes) < 1000:
            print("[STT] ⚠️ Audio too short after VAD trimming")
            return ""

        # Create BytesIO object for direct upload
        audio_buffer = BytesIO(audio_bytes)
        audio_buffer.seek(0)  # Ensure pointer is at beginning
        
        try:
            print(f"[STT] 📤 Transcribing {len(audio_bytes)} bytes...")
            ''' [TODO]
            # Use ElevenLabs SDK
            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,
                model_id=self.model,
                tag_audio_events=self.enable_audio_events,
                language_code=self.language_code,
                diarize=self.enable_diarize
            )
            '''
            language_code="eng"
            enable_diarize=False
            enable_audio_events=False

            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,  # BytesIO directly - faster!
                model_id="scribe_v1",
                tag_audio_events=enable_audio_events,
                language_code=language_code,
                diarize=enable_diarize
            )

            text = transcription.text.strip()
            
            if text:
                print(f"[STT] ✅ Transcription: {text}")
            else:
                print("[STT] ⚠️ Empty transcription received")
            
            return text
            
        except Exception as e:
            print(f"[STT] ❌ Transcription error: {e}")
            return ""

    def transcribe_file(self, path: str) -> str:
        """
        Transcribe audio from file
        
        Args:
            path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not path or not os.path.isfile(path):
            return ""
            
        ext = os.path.splitext(path)[1].lower()
        
        # Convert non-WAV files to WAV if ffmpeg is available
        if ext not in [".wav", ".mp3", ".flac", ".m4a"] and self._can_ffmpeg:
            wav_path = os.path.join(self._tmp_dir, f"{uuid.uuid4().hex}.wav")
            try:
                if _ffmpeg_convert(path, wav_path):
                    with open(wav_path, "rb") as f:
                        audio_bytes = f.read()
                    os.remove(wav_path)
                    return self.transcribe_bytes(audio_bytes, is_wav=True)
            except Exception as e:
                print(f"[STT] ⚠️ Conversion failed: {e}")
                try:
                    os.remove(wav_path)
                except:
                    pass
        
        # Read file directly and transcribe
        try:
            with open(path, "rb") as f:
                audio_bytes = f.read()
            
            # If it's already a WAV, use transcribe_bytes
            if ext == ".wav":
                return self.transcribe_bytes(audio_bytes, is_wav=True)
            
            # For other formats, create BytesIO and use SDK directly
            audio_buffer = BytesIO(audio_bytes)
            audio_buffer.seek(0)
            
            print(f"[STT] 📤 Transcribing file: {os.path.basename(path)} ({len(audio_bytes)} bytes)")
            
            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,
                model_id=self.model,
                tag_audio_events=self.enable_audio_events,
                language_code=self.language_code,
                diarize=self.enable_diarize
            )
            
            text = transcription.text.strip()
            
            if text:
                print(f"[STT] ✅ Transcription: {text}")
            
            return text
            
        except Exception as e:
            print(f"[STT] ❌ File transcription error: {e}")
            return ""

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.isdir(self._tmp_dir):
                shutil.rmtree(self._tmp_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    # Test the STT
    cfg = Config()
    stt = SpeechToText(cfg)
    
    print("Recording 3 seconds...")
    wav_bytes = record_via_sounddevice(3.0)
    
    print("Transcribing...")
    result = stt.transcribe_bytes(wav_bytes, is_wav=True)
    
    if result:
        print(f"✅ Result: {result}")
    else:
        print("❌ No transcription")
    
    stt.cleanup()