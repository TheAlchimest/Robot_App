'''
1A - Speech to Text using Google's SpeechRecognition API - Quick Fix
'''

import speech_recognition as sr
import pygame

pygame.mixer.init()

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(5)

def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Adjusting for background noise... Please wait.")
            
            # IMPORTANT: Uncomment this line to adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("Listening ... Speak now!")
            
            # Add timeout and phrase time limit
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            
            print("Processing...")
            text = recognizer.recognize_google(audio)
            print("You said: " + text)
            return text
            
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said. Please try again.")
        return None
        
    except sr.WaitTimeoutError:
        print("No speech detected within the timeout period.")
        return None
        
    except sr.RequestError as e:
        print(f"Error with the speech recognition service: {e}")
        return None
        
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