'''
Audio Recording Module - Auto-stop on Silence
'''

import pyaudio
import wave
import math
import struct
from io import BytesIO


def get_rms(data):
    """حساب مستوى الصوت (RMS - Root Mean Square)"""
    count = len(data) / 2
    format_string = "%dh" % count
    shorts = struct.unpack(format_string, data)
    sum_squares = sum(s ** 2 for s in shorts)
    rms = math.sqrt(sum_squares / count)
    return rms


def is_silent(data, threshold=500):
    """التحقق من وجود صمت بناءً على مستوى الصوت"""
    return get_rms(data) < threshold


class AudioRecorder:
    """فئة لتسجيل الصوت مع الكشف التلقائي عن الصمت"""
    
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
    
    def record_fixed_duration(self, duration=3):
        """
        تسجيل صوت لمدة محددة
        
        Args:
            duration: مدة التسجيل بالثواني
        
        Returns:
            BytesIO: ملف الصوت في الذاكرة
        """
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print(f"🎤 Recording for {duration} seconds...")
            
            frames = []
            for i in range(0, int(self.RATE / self.CHUNK * duration)):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            print("✓ Recording complete!")
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        return self._create_wav_buffer(frames, p)
    
    def record_until_silence(
        self,
        silence_threshold=500,
        silence_duration=2.0,
        max_duration=30,
        min_duration=0.5
    ):
        """
        تسجيل الصوت حتى يتوقف المستخدم عن الكلام
        
        Args:
            silence_threshold: حد الصمت (300-800)
            silence_duration: مدة الصمت المطلوبة للتوقف (بالثواني)
            max_duration: الحد الأقصى لمدة التسجيل (بالثواني)
            min_duration: الحد الأدنى لمدة التسجيل (بالثواني)
        
        Returns:
            BytesIO: ملف الصوت في الذاكرة
        """
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("🎤 Listening... Speak now! (Will auto-stop when you finish)")
            
            frames = []
            silent_chunks = 0
            silent_chunks_required = int(self.RATE / self.CHUNK * silence_duration)
            max_chunks = int(self.RATE / self.CHUNK * max_duration)
            min_chunks = int(self.RATE / self.CHUNK * min_duration)
            started_speaking = False
            
            chunk_count = 0
            
            while chunk_count < max_chunks:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
                chunk_count += 1
                
                # التحقق من مستوى الصوت
                if is_silent(data, silence_threshold):
                    silent_chunks += 1
                    
                    # إذا بدأ المستخدم بالكلام ثم توقف
                    if started_speaking and silent_chunks >= silent_chunks_required:
                        if chunk_count >= min_chunks:
                            duration = chunk_count * self.CHUNK / self.RATE
                            print(f"✓ Silence detected. Stopping... ({duration:.1f}s)")
                            break
                else:
                    # المستخدم يتكلم
                    if not started_speaking:
                        print("🔊 Speech detected!")
                        started_speaking = True
                    silent_chunks = 0
            
            if chunk_count >= max_chunks:
                print(f"⚠️ Max duration reached ({max_duration}s)")
            
            if not started_speaking:
                print("⚠️ No speech detected")
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        return self._create_wav_buffer(frames, p)
    
    def calibrate_silence_threshold(self, duration=3):
        """
        معايرة حد الصمت بناءً على ضجيج الخلفية
        
        Args:
            duration: مدة المعايرة بالثواني
        
        Returns:
            int: الحد المقترح للصمت
        """
        p = pyaudio.PyAudio()
        
        print("🔧 Calibrating... Please stay silent")
        
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            rms_values = []
            for i in range(0, int(self.RATE / self.CHUNK * duration)):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                rms_values.append(get_rms(data))
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        avg_rms = sum(rms_values) / len(rms_values)
        suggested_threshold = int(avg_rms * 3)
        
        print(f"✓ Background noise: {avg_rms:.0f}")
        print(f"✓ Suggested threshold: {suggested_threshold}")
        
        return suggested_threshold
    
    def _create_wav_buffer(self, frames, pyaudio_instance):
        """إنشاء ملف WAV في الذاكرة"""
        audio_buffer = BytesIO()
        with wave.open(audio_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(pyaudio_instance.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        audio_buffer.seek(0)
        return audio_buffer