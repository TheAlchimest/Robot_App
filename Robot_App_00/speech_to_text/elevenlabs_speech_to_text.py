'''
Speech to Text using ElevenLabs API - Optimized Version
'''

import pyaudio
import wave
from io import BytesIO
from elevenlabs.client import ElevenLabs
from Config import Config

# تحميل الإعدادات
config = Config()

# تهيئة ElevenLabs
elevenlabs = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)


def record_audio(duration=3):
    """تسجيل الصوت وإرجاعه في الذاكرة مباشرة"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print("🎤 Listening... Speak now!")
        
        # تسجيل الصوت
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        print("✓ Recording complete!")
        
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    # إنشاء ملف WAV في الذاكرة
    audio_buffer = BytesIO()
    with wave.open(audio_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    audio_buffer.seek(0)
    return audio_buffer


def listen(duration=3, enable_diarize=False, enable_audio_events=False):
    """
    الاستماع وتحويل الصوت إلى نص
    
    Args:
        duration: مدة التسجيل بالثواني (افتراضي: 3)
        enable_diarize: تحديد المتحدث (افتراضي: False)
        enable_audio_events: تحديد الأحداث الصوتية مثل الضحك (افتراضي: False)
    
    Returns:
        str: النص المحول أو None في حالة الفشل
    """
    try:
        # تسجيل الصوت
        audio_buffer = record_audio(duration=duration)
        
        print("⚙️ Processing...")
        
        # تحويل الصوت إلى نص
        transcription = elevenlabs.speech_to_text.convert(
            file=audio_buffer,
            model_id="scribe_v1",
            tag_audio_events=enable_audio_events,
            language_code="eng",
            diarize=enable_diarize
        )
        
        text = transcription.text.strip()
        
        if text:
            print(f"✓ You said: {text}")
            return text
        else:
            print("⚠️ No speech detected")
            return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def listen_continuous(max_attempts=3):
    """الاستماع المستمر مع إعادة المحاولة"""
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")
        result = listen()
        if result:
            return result
        print("Retrying...")
    
    print("❌ Failed after all attempts")
    return None


# ========== MAIN ===========

if __name__ == "__main__":
    print("=" * 50)
    print("ElevenLabs Speech-to-Text (Optimized)")
    print("=" * 50)
    
    # استخدام بسيط
    result = listen(duration=3)
    
    if result:
        print(f"\n✅ Final result: {result}")
    else:
        print("\n❌ Speech recognition failed")
    
    # أو استخدم الاستماع المستمر
    # result = listen_continuous(max_attempts=3)