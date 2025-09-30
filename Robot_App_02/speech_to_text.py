'''
Speech to Text Module using ElevenLabs API - Optimized
'''

from elevenlabs.client import ElevenLabs
from Config import Config
from io import BytesIO


class SpeechToText:
    """Class for converting audio to text using ElevenLabs"""
    
    def __init__(self, api_key=None):
        """
        Args:
            api_key: API key (optional, will load from Config if not provided)
        """
        if api_key is None:
            config = Config()
            api_key = config.ELEVENLABS_API_KEY
        
        self.client = ElevenLabs(api_key=api_key)
    
    def convert(
        self,
        audio_buffer,  # BytesIO - file in memory (faster!)
        language_code="eng",
        enable_diarize=False,
        enable_audio_events=False
    ):
        """
        Convert audio to text
        
        Args:
            audio_buffer: BytesIO - audio file in memory (faster than files!)
            language_code: Language code (eng, ara, etc)
            enable_diarize: Enable speaker identification
            enable_audio_events: Enable audio events detection
        
        Returns:
            str: Converted text or None if failed
        """
        try:
            print("⚙️ Converting speech to text...")
            
            # Ensure pointer is at the beginning of file
            if isinstance(audio_buffer, BytesIO):
                audio_buffer.seek(0)
            
            transcription = self.client.speech_to_text.convert(
                file=audio_buffer,  # BytesIO directly - faster!
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
        file_path,  # File path on disk
        language_code="eng",
        enable_diarize=False,
        enable_audio_events=False
    ):
        """
        Convert audio file from disk to text
        (Use this function only if file already exists on disk)
        
        Args:
            file_path: Audio file path
        
        Returns:
            str: Converted text
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
        Convert audio to text with additional details
        
        Args:
            audio_buffer: BytesIO - audio file in memory
        
        Returns:
            dict: {
                'text': str,
                'raw_response': object,
                'success': bool
            }
        """
        try:
            print("⚙️ Converting speech to text (detailed)...")
            
            # Ensure pointer is at the beginning of file
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