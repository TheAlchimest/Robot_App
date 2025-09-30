import io
import pygame
from typing import Literal
from openai import OpenAI
from Config import Config
config = Config()

client = OpenAI(api_key=config.OPEN_AI_API_KEY)




def play_audio(audio_bytes):
    """
    Plays audio content using pygame.

    Args:
        audio_bytes (bytes): Binary audio content to play.
    """
    pygame.mixer.init()
    pygame.mixer.music.load(io.BytesIO(audio_bytes))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def text_to_speech(text):
    """
    Converts text to speech using OpenAI's Text-to-Speech API.

    Args:
        text (str): Text to convert to speech.
    """
    # voice = "shimmer"
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "echo"
    response = client.audio.speech.create(model="tts-1", voice=voice, input=text)
    play_audio(response.read())


if __name__ == "__main__":
   pygame.init()
   text_to_speech("صباح الخير")
