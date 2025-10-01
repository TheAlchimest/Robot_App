"""
Configuration Manager - Singleton Pattern
Handles all system configurations and environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Singleton configuration class for system-wide settings"""
    
    _instance = None  # Holds the singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_env()
        return cls._instance

    def _load_env(self):
        """Load and validate environment variables"""
        self.DEVICE_ID = "123456000_1"
        
        # API Keys
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
        self.ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

        # Display Settings (for face tracking if used)
        self.SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", "1920"))
        self.SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", "1080"))
        self.SCREEN_MOVEMENT = int(os.getenv("SCREEN_MOVEMENT", "1920"))
        
        # File Paths
        self.MEMORY_FILE = os.getenv("MEMORY_FILE", "chat-memory.json")
        
        # AI Assistant Prompt
        self.ROBOT_PROMPT = (
            """
            Act as my personal AI assistant named Salim, designed to interact with me in a concise and informative manner.

            Guidelines:
            1. Identify yourself as "Salim, your personal AI assistant" when asked.
            2. Always respond politely and concisely (maximum 2-3 sentences), avoiding lengthy explanations.
            3. Maintain full context across the conversation; never mention memory lapses.
            4. Begin each reply with "Dear [Name]" if the user's name is known, otherwise use a respectful general greeting.
            5. Match the user's language (Arabic or English) in every response.
            6. For each interaction, classify the response as "Important" or "Not Important" based on:
               - Important: Personal data (names, birthdays, locations, hobbies), urgent/critical matters, schedules, or emotionally intense content.
               - Not Important: Casual chat, trivia, low-priority, or non-actionable info.
            7. Always format your reply strictly as:
               [Status, Response]

            Examples:
            [Important, I have noted this critical task Mr. Jon.]
            [Not Important, That's fine! Thank you for sharing.]
            """
        )
        
        # Audio Settings
        self.AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "512"))
        self.AUDIO_RATE = int(os.getenv("AUDIO_RATE", "16000"))
        self.AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
        self.SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "500"))
        self.SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "1.5"))
        
        # AI Model Settings
        self.AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "150"))
        self.AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
        
        # TTS Settings
        self.TTS_MODEL = os.getenv("TTS_MODEL", "eleven_turbo_v2_5")
        self.TTS_VOICE = os.getenv("TTS_VOICE", "adam")
        
        # Memory Settings
        self.MEMORY_LIMIT = int(os.getenv("MEMORY_LIMIT", "10000"))
        self.MEMORY_CONTEXT_SIZE = int(os.getenv("MEMORY_CONTEXT_SIZE", "5"))
        
        # System Settings
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # Validate critical API keys
        self._validate_keys()

    def _validate_keys(self):
        """Validate that critical API keys are present"""
        if not self.OPEN_AI_API_KEY:
            raise ValueError("❌ Missing OPEN_AI_API_KEY in environment variables")
        
        if not self.ELEVENLABS_API_KEY:
            raise ValueError("❌ Missing ELEVENLABS_API_KEY in environment variables")
        
        print("✅ API keys validated successfully")

    def get_audio_config(self):
        """Get audio recording configuration"""
        return {
            'chunk_size': self.AUDIO_CHUNK_SIZE,
            'rate': self.AUDIO_RATE,
            'channels': self.AUDIO_CHANNELS,
            'silence_threshold': self.SILENCE_THRESHOLD,
            'silence_duration': self.SILENCE_DURATION
        }

    def get_ai_config(self):
        """Get AI model configuration"""
        return {
            'model': self.AI_MODEL,
            'max_tokens': self.AI_MAX_TOKENS,
            'temperature': self.AI_TEMPERATURE
        }

    def get_tts_config(self):
        """Get TTS configuration"""
        return {
            'model': self.TTS_MODEL,
            'voice': self.TTS_VOICE
        }

    def get_memory_config(self):
        """Get memory management configuration"""
        return {
            'memory_file': self.MEMORY_FILE,
            'memory_limit': self.MEMORY_LIMIT,
            'context_size': self.MEMORY_CONTEXT_SIZE
        }

    def print_config(self):
        """Print current configuration (for debugging)"""
        print("\n" + "="*60)
        print("⚙️  SYSTEM CONFIGURATION")
        print("="*60)
        print(f"AI Model: {self.AI_MODEL}")
        print(f"Max Tokens: {self.AI_MAX_TOKENS}")
        print(f"TTS Model: {self.TTS_MODEL}")
        print(f"TTS Voice: {self.TTS_VOICE}")
        print(f"Audio Rate: {self.AUDIO_RATE}")
        print(f"Chunk Size: {self.AUDIO_CHUNK_SIZE}")
        print(f"Memory Limit: {self.MEMORY_LIMIT}")
        print(f"Context Size: {self.MEMORY_CONTEXT_SIZE}")
        print(f"Debug Mode: {self.DEBUG_MODE}")
        print("="*60 + "\n")


# Quick test
if __name__ == "__main__":
    try:
        config = Config()
        config.print_config()
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
