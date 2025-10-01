'''
Audio Recording Module - Performance Optimized
'''

import pyaudio
import wave
import math
import struct
from io import BytesIO

def get_rms(data):
    """Calculate audio level (RMS - Root Mean Square)"""
    count = len(data) // 2
    if count == 0:
        return 0
    format_string = f"{count}h"
    shorts = struct.unpack(format_string, data)
    sum_squares = sum(s ** 2 for s in shorts)
    return math.sqrt(sum_squares / count)

def is_silent(data, threshold=500):
    """Check for silence based on audio level"""
    return get_rms(data) < threshold

class AudioRecorder:
    """Optimized audio recording class"""
    
    def __init__(self):
        self.CHUNK = 512  # Smaller chunk size for faster response
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.p = None
        self.stream = None
    
    def _init_stream(self):
        """Initialize stream once"""
        if self.p is None:
            self.p = pyaudio.PyAudio()
        if self.stream is None:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
    
    def record_until_silence(
        self,
        silence_threshold=500,
        silence_duration=1.5,
        max_duration=20,
        min_duration=0.3
    ):
        """
        Optimized recording with faster response
        
        Args:
            silence_threshold: Silence threshold (300-800)
            silence_duration: Required silence duration to stop (seconds)
            max_duration: Maximum recording duration (seconds)
            min_duration: Minimum recording duration (seconds)
        
        Returns:
            BytesIO: Audio file in memory
        """
        self._init_stream()
        
        frames = []
        silent_chunks = 0
        silent_chunks_required = int(self.RATE / self.CHUNK * silence_duration)
        max_chunks = int(self.RATE / self.CHUNK * max_duration)
        min_chunks = int(self.RATE / self.CHUNK * min_duration)
        started_speaking = False
        
        chunk_count = 0
        
        print("🎤 Ready to listen...")
        
        while chunk_count < max_chunks:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            chunk_count += 1
            
            if is_silent(data, silence_threshold):
                silent_chunks += 1
                
                if started_speaking and silent_chunks >= silent_chunks_required:
                    if chunk_count >= min_chunks:
                        duration = chunk_count * self.CHUNK / self.RATE
                        print(f"✓ Recording completed ({duration:.1f}s)")
                        break
            else:
                if not started_speaking:
                    print("🔊 Speech detected...")
                    started_speaking = True
                silent_chunks = 0
        
        return self._create_wav_buffer(frames)
    
    def _create_wav_buffer(self, frames):
        """Create WAV file in memory"""
        audio_buffer = BytesIO()
        with wave.open(audio_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        audio_buffer.seek(0)
        return audio_buffer
    
    def cleanup(self):
        """Cleanup resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
    
    def __del__(self):
        """Automatic cleanup"""
        self.cleanup()
