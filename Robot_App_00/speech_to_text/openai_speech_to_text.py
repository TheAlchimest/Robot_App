'''
Speech to Text using OpenAI Whisper API - Alternative Version
'''

import pyaudio
import wave
from openai import OpenAI
import tempfile
import os
import pygame
# Load environment variables from .env file
from Config import Config
config = Config()



pygame.mixer.init()

client = OpenAI(api_key=config.OPEN_AI_API_KEY)

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(5)

def record_audio(duration=5):
    """تسجيل الصوت باستخدام pyaudio"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    print("Listening ... Speak now!")
    
    frames = []
    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # حفظ الملف الصوتي
    temp_filename = tempfile.mktemp(suffix=".wav")
    wf = wave.open(temp_filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return temp_filename



def listen():
    try:
        print("Adjusting for background noise... Please wait.")
        
        # تسجيل الصوت
        temp_filename = record_audio(duration=5)
        
        print("Processing...")
        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        text = transcript.text
        print("You said: " + text)

        # حذف الملف المؤقت
        os.unlink(temp_filename)
        return text
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

##--------MAIN-----------

if __name__ == "__main__":
    result = listen()
    if result:
        print(f"Final result: {result}")
    else:
        print("Speech recognition failed.")