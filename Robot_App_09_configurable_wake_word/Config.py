# Config.py
# تحسينات: قيم افتراضية محسّنة، validation أفضل، performance tuning

import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    ALLOW_INTERRUPTION = os.getenv("ALLOW_INTERRUPTION", "False").lower() == "true"
    ALLOW_WAKE_WORD = os.getenv("ALLOW_WAKE_WORD", "False").lower() == "true"
    DEVICE = os.getenv("DEVICE", "raspi5").strip()
    EYE_MODEL = os.getenv("EYE_MODEL", "img").strip()

    # === API Keys (Required) ===
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
    N8N_URL = os.getenv("N8N_URL", "").strip()

    # === STT Settings ===
    ELEVEN_STT_URL = os.getenv(
        "ELEVEN_STT_URL",
        "https://api.elevenlabs.io/v1/speech-to-text"
    ).strip()
    ELEVEN_STT_MODEL = os.getenv("ELEVEN_STT_MODEL", "scribe_v1").strip()

    # === Interruption Settings ===
    ALLOW_INTERRUPTION = os.getenv("ALLOW_INTERRUPTION", "False").strip().lower() in ("true", "1", "yes")


    # === TTS Voice Mapping ===
    VOICE_IDS = {
        "adam": os.getenv("ELEVEN_VOICE_ADAM", "pNInz6obpgDQGcFmaJgB"),
        "rachel": os.getenv("ELEVEN_VOICE_RACHEL", "21m00Tcm4TlvDq8ikWAM"),
    }
    DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "adam").strip()

    # === Audio Backend ===
    AUDIO_BACKEND = os.getenv("AUDIO_BACKEND", "").strip().lower()
    AUDIO_DEVICE = os.getenv("AUDIO_DEVICE", "default").strip()

    # === Performance Settings ===
    STATUS_MONITOR = os.getenv("STATUS_MONITOR", "0").strip() in ("1", "true", "yes")

    # === Recorder Settings (16k/mono/16-bit) ===
    REC_SAMPLE_RATE = int(os.getenv("REC_SAMPLE_RATE", "16000"))
    REC_CHANNELS = 1
    REC_WIDTH = 2
    
    # ✅ Chunk size محسّن: أصغر = استجابة أسرع
    REC_CHUNK = int(os.getenv("REC_CHUNK", "256"))  # كان 512

    # === VAD / Silence Detection (محسّنة) ===
    # ✅ Threshold أعلى قليلاً لتقليل false positives
    SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "600"))  # كان 500
    
    # ✅ Duration أقصر للاستجابة الأسرع
    SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "0.8"))  # كان 1.0
    
    # ✅ Max duration أقصر لتجنب التأخير
    MAX_RECORD_SEC = float(os.getenv("MAX_RECORD_SEC", "10.0"))  # كان 12.0
    
    # ✅ Min duration أقصر للتجاوب الأسرع
    MIN_RECORD_SEC = float(os.getenv("MIN_RECORD_SEC", "0.2"))  # كان 0.25

    # === Network Settings (محسّنة) ===
    # ✅ Timeout أقصر للـ responsiveness
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))  # كان 30
    
    # ✅ Retries أقل للسرعة
    RETRIES = int(os.getenv("HTTP_RETRIES", "2"))  # كان 3

    # === Camera Settings (لو استخدمت Face Tracking) ===
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_FLIP = os.getenv("CAMERA_FLIP", "False").strip().lower() in ("true", "1", "yes")

    # === Validation ===
    def __init__(self):
        errors = []
        
        if not self.ELEVENLABS_API_KEY:
            errors.append("❌ Missing ELEVENLABS_API_KEY")
        
        if not self.N8N_URL:
            errors.append("❌ Missing N8N_URL")
        
        # ✅ Validation للقيم
        if self.REC_SAMPLE_RATE not in [8000, 16000, 22050, 44100, 48000]:
            errors.append(f"⚠️ Invalid REC_SAMPLE_RATE: {self.REC_SAMPLE_RATE}")
        
        if self.REC_CHUNK < 128 or self.REC_CHUNK > 2048:
            errors.append(f"⚠️ REC_CHUNK should be between 128-2048: {self.REC_CHUNK}")
        
        if self.SILENCE_THRESHOLD < 100 or self.SILENCE_THRESHOLD > 2000:
            errors.append(f"⚠️ SILENCE_THRESHOLD seems off: {self.SILENCE_THRESHOLD}")
        
        if errors:
            print("\n".join(errors))
            if any("❌" in e for e in errors):
                raise ValueError("Configuration errors found!")

    def print_settings(self):
        """طباعة الإعدادات الحالية (للتشخيص)"""
        print("\n" + "=" * 50)
        print("⚙️  CONFIGURATION")
        print("=" * 50)
        print(f"STT Model: {self.ELEVEN_STT_MODEL}")
        print(f"TTS Voice: {self.DEFAULT_VOICE}")
        print(f"Sample Rate: {self.REC_SAMPLE_RATE} Hz")
        print(f"Chunk Size: {self.REC_CHUNK} frames")
        print(f"Silence Threshold: {self.SILENCE_THRESHOLD} RMS")
        print(f"Silence Duration: {self.SILENCE_DURATION}s")
        print(f"Max Record: {self.MAX_RECORD_SEC}s")
        print(f"HTTP Timeout: {self.HTTP_TIMEOUT}s")
        print(f"Retries: {self.RETRIES}")
        print("=" * 50 + "\n")
