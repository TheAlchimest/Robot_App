'''
Speech to Text Module using ElevenLabs API - Optimized
'''

from elevenlabs.client import ElevenLabs
from Config import Config
from io import BytesIO


class SpeechToText:
    """فئة لتحويل الصوت إلى نص باستخدام ElevenLabs"""
    
    def __init__(self, api_key=None):
        """
        Args:
            api_key: مفتاح API (اختياري، سيتم تحميله من Config إذا لم يتم توفيره)
        """
        if api_key is None:
            config = Config()
            api_key = config.ELEVENLABS_API_KEY
        
        self.client = ElevenLabs(api_key=api_key)
    
    def convert(
        self,
        audio_buffer,  # BytesIO - ملف في الذاكرة (أسرع!)
        language_code="eng",
        enable_diarize=False,
        enable_audio_events=False
    ):
        """
        تحويل الصوت إلى نص
        
        Args:
            audio_buffer: BytesIO - ملف صوتي في الذاكرة (أسرع من الملفات!)
            language_code: رمز اللغة (eng, ara, etc)
            enable_diarize: تحديد المتحدث
            enable_audio_events: تحديد الأحداث الصوتية
        
        Returns:
            str: النص المحول أو None في حالة الفشل
        """
        try:
            print("⚙️ Converting speech to text...")
            
            # تأكد من أن المؤشر في بداية الملف
            if isinstance(audio_buffer, BytesIO):
                audio_buffer.seek(0)
            
            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,  # BytesIO مباشرة - أسرع!
                model_id="scribe_v1",
                tag_audio_events=enable_audio_events,
                language_code=language_code,
                diarize=enable_diarize
            )
            
            text = transcription.text.strip()
            
            if text:
                print(f"✅ Transcription: {text}")
                return text
            else:
                print("⚠️ Empty transcription")
                return None
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def convert_from_file(
        self,
        file_path,  # مسار الملف على القرص
        language_code="eng",
        enable_diarize=False,
        enable_audio_events=False
    ):
        """
        تحويل ملف صوتي من القرص إلى نص
        (استخدم هذه الدالة فقط إذا كان الملف موجود مسبقاً على القرص)
        
        Args:
            file_path: مسار الملف الصوتي
        
        Returns:
            str: النص المحول
        """
        try:
            print("⚙️ Converting speech to text from file...")
            
            with open(file_path, "rb") as audio_file:
                transcription = self.client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v1",
                    tag_audio_events=enable_audio_events,
                    language_code=language_code,
                    diarize=enable_diarize
                )
            
            text = transcription.text.strip()
            
            if text:
                print(f"✅ Transcription: {text}")
                return text
            else:
                print("⚠️ Empty transcription")
                return None
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def convert_with_details(
        self,
        audio_buffer,
        language_code="eng",
        enable_diarize=False,
        enable_audio_events=False
    ):
        """
        تحويل الصوت إلى نص مع تفاصيل إضافية
        
        Args:
            audio_buffer: BytesIO - ملف صوتي في الذاكرة
        
        Returns:
            dict: {
                'text': str,
                'raw_response': object,
                'success': bool
            }
        """
        try:
            print("⚙️ Converting speech to text (detailed)...")
            
            # تأكد من أن المؤشر في بداية الملف
            if isinstance(audio_buffer, BytesIO):
                audio_buffer.seek(0)
            
            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,
                model_id="scribe_v1",
                tag_audio_events=enable_audio_events,
                language_code=language_code,
                diarize=enable_diarize
            )
            
            text = transcription.text.strip()
            
            return {
                'text': text if text else None,
                'raw_response': transcription,
                'success': bool(text)
            }
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return {
                'text': None,
                'raw_response': None,
                'success': False,
                'error': str(e)
            }