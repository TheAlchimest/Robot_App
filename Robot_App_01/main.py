# ------------------- Import Libraries -------------------
#from speech_to_text import elevenlabs_speech_to_text as stt
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText

import text_to_speech as tts
import ai_model as llm
import pygame

# Create objects
recorder = AudioRecorder()
stt = SpeechToText()


def main2():
    # For constantly listening to user
    pygame.init()
    tts.text_to_speech("Hello How can I help you today?")
    print("main2")

    while True:

        # تسجيل الصوت في الذاكرة (BytesIO) - سريع! ⚡
        audio_buffer = recorder.record_until_silence()
        user_input = stt.convert(audio_buffer)

        if user_input:
            print(f"Final result: {user_input}")
        else:
            print("Speech recognition failed.")


        response  =  llm.chat(user_input)
        
        tts.text_to_speech(response)







main2()

