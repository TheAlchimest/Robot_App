# audio_recorder.py
# تحسينات: VAD أفضل مع smoothing، fallback محسّن، circular buffer

import io
import time
import audioop
import subprocess
import collections
from typing import Optional

from Config import Config

try:
    import pyaudio
    _HAS_PYAUDIO = True
except Exception:
    _HAS_PYAUDIO = False

class AudioRecorder:
    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.rate = self.cfg.REC_SAMPLE_RATE
        self.width = self.cfg.REC_WIDTH
        self.channels = self.cfg.REC_CHANNELS
        self.chunk = self.cfg.REC_CHUNK

        self._pa = None
        self._stream = None
        
        # ✅ Smoothing buffer للـ RMS (تقليل false positives)
        self._rms_history = collections.deque(maxlen=5)

        if _HAS_PYAUDIO:
            try:
                self._pa = pyaudio.PyAudio()
                print("[Recorder] ✅ PyAudio initialized")
            except Exception as e:
                print(f"[Recorder] ⚠️ PyAudio failed: {e}")
                self._pa = None
        
        if not self._pa:
            print("[Recorder] ℹ️ Using 'arecord' fallback")

    def close(self):
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if self._pa:
                self._pa.terminate()
        except Exception:
            pass

    def _get_smoothed_rms(self, data: bytes) -> float:
        """حساب RMS مع smoothing لتقليل التذبذب"""
        try:
            rms = audioop.rms(data, self.width) if data else 0
        except Exception:
            rms = 0
        
        self._rms_history.append(rms)
        
        # ✅ استخدام median بدلاً من average (أفضل ضد الـ spikes)
        sorted_rms = sorted(self._rms_history)
        return sorted_rms[len(sorted_rms) // 2]

    def _has_voice_activity(self, rms: float, threshold: int) -> bool:
        """كشف الصوت مع hysteresis لتجنب الـ flickering"""
        # ✅ استخدام هامش (margin) للثبات
        if hasattr(self, '_last_voice_state'):
            if self._last_voice_state:
                # إذا كان هناك صوت، نحتاج انخفاض أكبر للتوقف
                threshold_low = threshold * 0.7
                has_voice = rms >= threshold_low
            else:
                # إذا لم يكن هناك صوت، نحتاج ارتفاع أكبر للبدء
                threshold_high = threshold * 1.3
                has_voice = rms >= threshold_high
        else:
            has_voice = rms >= threshold
        
        self._last_voice_state = has_voice
        return has_voice

    def record_until_silence(
        self,
        silence_threshold: Optional[int] = None,
        silence_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        min_duration: Optional[float] = None
    ) -> bytes:
        """
        تسجيل حتى اكتشاف صمت مع VAD محسّن
        """
        silence_threshold = silence_threshold or self.cfg.SILENCE_THRESHOLD
        silence_duration = silence_duration or self.cfg.SILENCE_DURATION
        max_duration = max_duration or self.cfg.MAX_RECORD_SEC
        min_duration = min_duration or self.cfg.MIN_RECORD_SEC

        pcm_buf = io.BytesIO()
        frames_per_second = max(1, int(self.rate / self.chunk))
        silent_chunks_needed = max(1, int(silence_duration * frames_per_second))

        start_t = time.time()
        trailing_silent = 0
        
        # ✅ إعادة تعيين الـ history
        self._rms_history.clear()
        self._last_voice_state = False

        use_pa = self._pa is not None
        
        if use_pa:
            try:
                self._stream = self._pa.open(
                    format=self._pa.get_format_from_width(self.width),
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
            except Exception as e:
                print(f"[Recorder] ❌ PyAudio stream failed: {e}")
                use_pa = False

        try:
            while True:
                elapsed = time.time() - start_t
                if elapsed >= max_duration:
                    break

                if use_pa:
                    try:
                        data = self._stream.read(self.chunk, exception_on_overflow=False)
                    except Exception as e:
                        print(f"[Recorder] ⚠️ Read error: {e}")
                        break
                else:
                    # ✅ Fallback محسّن: chunks أصغر
                    data = self._record_chunk_arecord(duration=0.1)
                    if not data:
                        break

                pcm_buf.write(data)

                # ✅ VAD محسّن مع smoothing
                rms = self._get_smoothed_rms(data)
                has_voice = self._has_voice_activity(rms, silence_threshold)

                if not has_voice:
                    trailing_silent += 1
                else:
                    trailing_silent = 0

                # ✅ التوقف عند اكتمال الشروط
                if trailing_silent >= silent_chunks_needed and elapsed >= min_duration:
                    break

        finally:
            if use_pa and self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

        raw_pcm = pcm_buf.getvalue()
        
        # ✅ فحص الحد الأدنى للطول
        if len(raw_pcm) < int(self.rate * min_duration * self.width):
            return b""

        return self._wrap_to_wav(raw_pcm)

    def _record_chunk_arecord(self, duration: float = 0.1) -> bytes:
        """تسجيل chunk قصير باستخدام arecord"""
        cmd = [
            "arecord",
            "-q",
            "-c", str(self.channels),
            "-r", str(self.rate),
            "-f", "S16_LE",
            "-d", f"{duration:.2f}",  # ✅ دقة أعلى
            "-t", "raw"
        ]
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=duration + 0.5)
        except Exception:
            return b""

    def _wrap_to_wav(self, raw_pcm: bytes) -> bytes:
        """تحويل PCM إلى WAV"""
        import wave
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.width)
            wf.setframerate(self.rate)
            wf.writeframes(raw_pcm)
        return out.getvalue()
