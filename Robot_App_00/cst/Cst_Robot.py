"""
Speech with emotions

Requirements:
    - pip install -r req.txt

This script requires Robot to be connected through HDMI. Arduino USB ports, and
external power as well
"""

# ------------------- Import Libraries -------------------
import tempfile
import io
from typing import Literal
import httpx, ssl, os
import google.generativeai as genai
import pygame
import speech_recognition as sr
from openai import OpenAI


from time import sleep
import threading
import cv2


import Speech_to_text  as stt
import cst_api_client as api
import speech_to_text.google_speech_to_text as gt
# Load environment variables from .env file
from Config import Config
config = Config()
# ------------------- Servo Movements



# Initialize the last known positions for the three servos: Left (LServo), Right (RServo), Head (HServo)
# LServo starts at 180 degrees, RServo at 0 degrees, and HServo at 90 degrees
last_positions = [180, 0, 90]

switch_video = False
# Global flag to stop video playback
stop_video_event = threading.Event()


# ------------------- Configurations -------------------

# Configure API keys
genai.configure(api_key=config.GEMINI_API_KEY)



API_KEY = config.OPEN_AI_API_KEY

# سياق SSL بدون تحقق
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Transport يجبر HTTP/1.1 ويستخدم الـ ctx
transport = httpx.HTTPTransport(retries=0, verify=ctx)
session = httpx.Client(transport=transport, timeout=30, http2=False)

client = OpenAI(api_key=API_KEY, http_client=session)




# ------------------- screen setup -------------------
screen_width = int(config.SCREEN_WIDTH)
screen_height = int(config.SCREEN_HEIGHT)
screen_movement = int(config.SCREEN_MOVEMENT)
# ------------------- AI Prompt -------------------

# ------------------- AI Prompt -------------------


# ------------------- Text-to-Speech Function -------------------

def text_to_speech(text):
    # تقدر تختار أي صوت من اللي متاحين، مثلا "nova"
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "echo"
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    # تشغيل الصوت
    play_audio(response.read())
    
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



#===========================Gesture Integration================================

# ------------------- Movement Functions --------------------------------------

#=========================Emotion intergation==============================

# --------------------thread function--------------------
def ai_to_speech(user_input):
    ai_response = ai_model_response(user_input)
    print(f"AI Response: {ai_response}")
    text_to_speech(ai_response)


# ======================MAIN==========================

pygame.init()

text_to_speech("Hello, I'm Salem, your personal assistant.")


# For constantly listening to user
while True:


    #user_input = stt.speech_to_text_multilingual()
    user_input = gt.listen_with_google()
    
    print(user_input)
    if user_input:
        # Normal conversation flow
        ai_response =api.send_message("ef604e99-3f60-42a3-b773-09e2811b3dc3", user_input)
        print(f"AI Response: {ai_response}")
        text_to_speech(ai_response)

