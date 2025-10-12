# Config.py
# -------------------------------------------------------------------
# Centralized configuration with sensible defaults for Raspberry Pi.
# Reads from environment when available. Keeps non-blocking validation.
# -------------------------------------------------------------------

import os

class Config:
    # === Required / API Keys ===
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
    # n8n endpoint that returns JSON: { activeAgent?: "...", output: "..." }
    N8N_URL            = os.getenv("N8N_URL", "").strip()

    # === Optional: STT model/URL (ElevenLabs) ===
    ELEVEN_STT_URL     = os.getenv("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text").strip()
    ELEVEN_STT_MODEL   = os.getenv("ELEVEN_STT_MODEL", "eleven_multilingual_v2").strip()

    # === TTS voices mapping (name -> eleven voice_id) ===
    VOICE_IDS = {
        # put your own ids here
        "adam":  os.getenv("ELEVEN_VOICE_ADAM",  "Adam"),
        "bella": os.getenv("ELEVEN_VOICE_BELLA", "Bella"),
    }
    DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "adam").strip()

    # === Audio Playback Backend ===
    # "alsa" (pyalsaaudio), "aplay" (alsa-utils), "pygame"
    AUDIO_BACKEND = os.getenv("AUDIO_BACKEND", "").strip().lower()  # autodetect if empty
    AUDIO_DEVICE  = os.getenv("AUDIO_DEVICE", "default").strip()     # e.g., "default" or "hw:0,0"

    # === Performance / Behavior ===
    ENABLE_EYE_VIDEO     = os.getenv("ENABLE_EYE_VIDEO", "0").strip() in ("1", "true", "yes")
    STATUS_MONITOR       = os.getenv("STATUS_MONITOR", "0").strip() in ("1", "true", "yes")

    # Recorder (16k/mono/16-bit)
    REC_SAMPLE_RATE = int(os.getenv("REC_SAMPLE_RATE", "16000"))
    REC_CHANNELS    = 1
    REC_WIDTH       = 2      # bytes (16-bit)
    REC_CHUNK       = int(os.getenv("REC_CHUNK", "512"))  # 256/512/1024
    # VAD / Silence detection
    SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "500"))  # RMS
    SILENCE_DURATION  = float(os.getenv("SILENCE_DURATION", "1.0"))
    MAX_RECORD_SEC    = float(os.getenv("MAX_RECORD_SEC", "12.0"))
    MIN_RECORD_SEC    = float(os.getenv("MIN_RECORD_SEC", "0.25"))

    # Networking
    HTTP_TIMEOUT   = int(os.getenv("HTTP_TIMEOUT", "30"))
    RETRIES        = int(os.getenv("HTTP_RETRIES", "3"))

    # Validate only what is needed globally for boot
    def __init__(self):
        if not self.ELEVENLABS_API_KEY:
            raise ValueError("❌ Missing ELEVENLABS_API_KEY")
        if not self.N8N_URL:
            raise ValueError("❌ Missing N8N_URL")
