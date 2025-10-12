# audio_recorder.py
# -------------------------------------------------------------------
# Low-CPU audio recorder for Raspberry Pi with:
# - 16k/mono/16-bit samples
# - Silence detection via audioop.rms (fast)
# - Fallbacks: PyAudio if available, else 'arecord' via ALSA
# -------------------------------------------------------------------

import io
import time
import audioop
import subprocess
from typing import Optional

from Config import Config

try:
    import pyaudio
    _HAS_PYAUDIO = True
except Exception:
    _HAS_PYAUDIO = False

class AudioRecorder:
    def __init__(self, config: Config | None = None):
        self.cfg = config or Config()
        self.rate     = self.cfg.REC_SAMPLE_RATE
        self.width    = self.cfg.REC_WIDTH     # 2 bytes (16-bit)
        self.channels = self.cfg.REC_CHANNELS
        self.chunk    = self.cfg.REC_CHUNK     # frames per buffer

        self._pa = None
        self._stream = None

        if _HAS_PYAUDIO:
            self._pa = pyaudio.PyAudio()
        else:
            print("[Recorder] PyAudio not found. Will fallback to 'arecord' when needed.")

    def close(self):
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if self._pa:
                self._pa.terminate()
        except Exception:
            pass

    def _record_with_pyaudio(self, max_seconds: float) -> bytes:
        self._stream = self._pa.open(
            format=self._pa.get_format_from_width(self.width),
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        frames = []
        total_frames = int(self.rate / self.chunk * max_seconds)
        for _ in range(total_frames):
            data = self._stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)
        self._stream.stop_stream()
        self._stream.close()
        self._stream = None
        return b"".join(frames)

    def _record_with_arecord(self, seconds: float) -> bytes:
        cmd = [
            "arecord",
            "-q",
            "-c", str(self.channels),
            "-r", str(self.rate),
            "-f", "S16_LE",
            "-d", str(max(1, int(seconds))),
            "-t", "raw"   # raw PCM
        ]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            return out
        except Exception as e:
            print(f"[Recorder] arecord failed: {e}")
            return b""

    def record_until_silence(
        self,
        silence_threshold: int | None = None,
        silence_duration: float | None = None,
        max_duration: float | None = None,
        min_duration: float | None = None
    ) -> bytes:
        """
        Records audio until trailing silence is detected, with caps:
          - silence_threshold: RMS threshold
          - silence_duration: required trailing silence seconds
          - max_duration: hard cap seconds
          - min_duration: minimum length to accept
        Returns WAV (16k/mono/16-bit) bytes.
        """
        silence_threshold = silence_threshold if silence_threshold is not None else self.cfg.SILENCE_THRESHOLD
        silence_duration  = silence_duration if silence_duration is not None else self.cfg.SILENCE_DURATION
        max_duration      = max_duration if max_duration is not None else self.cfg.MAX_RECORD_SEC
        min_duration      = min_duration if min_duration is not None else self.cfg.MIN_RECORD_SEC

        pcm_buf = io.BytesIO()
        frames_per_second = max(1, int(self.rate / self.chunk))
        silent_chunks_needed = max(1, int(silence_duration * frames_per_second))

        start_t = time.time()
        trailing_silent = 0

        use_pa = _HAS_PYAUDIO
        if use_pa:
            self._stream = self._pa.open(
                format=self._pa.get_format_from_width(self.width),
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

        try:
            while True:
                elapsed = time.time() - start_t
                if elapsed >= max_duration:
                    break

                if use_pa:
                    data = self._stream.read(self.chunk, exception_on_overflow=False)
                else:
                    # Fallback chunk (1 sec granularity)
                    data = self._record_with_arecord(seconds=1.0)
                    if not data:
                        break

                pcm_buf.write(data)

                # Fast RMS
                try:
                    rms = audioop.rms(data, self.width) if data else 0
                except Exception:
                    rms = 0

                if rms < silence_threshold:
                    trailing_silent += 1
                else:
                    trailing_silent = 0

                if trailing_silent >= silent_chunks_needed and (time.time() - start_t) >= min_duration:
                    break

        finally:
            if use_pa:
                try:
                    if self._stream:
                        self._stream.stop_stream()
                        self._stream.close()
                except Exception:
                    pass
                self._stream = None

        raw_pcm = pcm_buf.getvalue()

        # Wrap PCM to WAV
        import wave
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.width)
            wf.setframerate(self.rate)
            wf.writeframes(raw_pcm)

        return out.getvalue()
