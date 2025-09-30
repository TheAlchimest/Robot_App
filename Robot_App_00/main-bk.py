"""
Speech with emotions

Requirements:
    - pip install -r req.txt

This script requires Robot to be connected through HDMI. Arduino USB ports, and
external power as well
"""

# ------------------- Import Libraries -------------------
from speech_to_text import openai_speech_to_text as stt
from text_to_speech import open_ai_text_to_speech as tts
from ai_models import google_gemini_model as ai
from ai_models import openai_model as gpt
from face_tracking import face_tracker as tracker
import pygame
import threading



tracker.trackUserFace(False)
print(f"trackUserFace")

# For constantly listening to user
while True:


    #user_input = stt.speech_to_text_multilingual()
    user_input = stt.listen()

    if user_input:
        print(f"Final result: {user_input}")
    else:
        print("Speech recognition failed.")


    pygame.init()
    response  =  gpt.chat(user_input)
    tts.text_to_speech(response)

    """
    print(user_input)
    if user_input:
        # Normal conversation flow
        ai_response =api.send_message("ef604e99-3f60-42a3-b773-09e2811b3dc3", user_input)
        print(f"AI Response: {ai_response}")
        text_to_speech(ai_response)
        """

