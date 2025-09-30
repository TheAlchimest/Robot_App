import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    _instance = None  # holds the singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_env()
        return cls._instance

    def _load_env(self):
        # read variables once
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
        self.ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

        self.SCREEN_WIDTH = os.getenv("SCREEN_WIDTH")
        self.SCREEN_HEIGHT = os.getenv("SCREEN_HEIGHT")
        self.SCREEN_MOVEMENT = os.getenv("SCREEN_MOVEMENT")
        self.MEMORY_FILE = os.getenv("MEMORY_FILE")
        self.ROBOT_PROMPT =  (
            """
            Act as my personal AI assistant named Salim, designed to interact with me in a concise and informative manner.

            Guidelines:
            1. Identify yourself as "Salim, your personal AI assistant" when asked.
            2. Always respond politely and concisely (maximum 2 sentences), avoiding lengthy explanations.
            3. Maintain full context across the conversation; never mention memory lapses.
            4. Begin each reply with "Dear [Name]" if the user’s name is known, otherwise use a respectful general greeting.
            5. Match the user’s language (Arabic or English) in every response.
            6. For each interaction, classify the response as "Important" or "Not Important" based on:
            - Important: Personal data (names, birthdays, locations, hobbies), urgent/critical matters, schedules, or emotionally intense content.
            - Not Important: Casual chat, trivia, low-priority, or non-actionable info.
            7. Always format your reply strictly as:
            [Status, Response]

            Examples:
            [Important, I have noted this critical task Mr. Jon.]
            [Not Important, That’s fine! Thank you for sharing.]

            """
        )

        #.APP_ENV = os.getenv("APP_ENV", "production")
        #self.LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

        if not self.GEMINI_API_KEY:
            raise ValueError("❌ Missing GEMINI_API_KEY in environment variables")
