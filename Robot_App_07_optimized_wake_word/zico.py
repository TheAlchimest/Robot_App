# ==================== AI Assistant System ====================
# Single-thread voice assistant (no threading)
# Wake Word: Ziko / زيكو
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
from local_commands import handle_local_command, extract_after_wake  # <== NEW
#import eye_runner as eye
import pygame
import os
import re
import sys
import time
import traceback
import threading
from queue import Queue, Empty

from Config import Config

# ------------------- Initialize Components -------------------
recorder = AudioRecorder()
stt = SpeechToText()
config = Config()



def cleanup():
        recorder.close()
        stt.cleanup()




    


# ================= Main Function =================
def main():
    pygame.init()
    index = 0
    
    while index <= 100 :
        index += 1
        try:

            print("Listening ...")
            # 1) Record
            audio_buffer = recorder.record_until_silence(
                max_duration=25.0,
                noise_calib_duration=0.8,
                start_frames=3,
                end_frames=15,            # جَرّب 18-22 لو لسه بيقطع
                post_silence_hold=0.35,
                pre_roll_ms=350,
                min_speech_after_start=1.8,
                threshold_boost=3.0       # قللها لو ما بيلتقطش أصوات منخفضة
            )
            if not audio_buffer:
                print("❌ there is no audio_buffer")
                continue

            
            # --- 2) Speech to Text ---
            try:
                user_input = stt.transcribe_bytes(audio_buffer)
            except Exception as ex:
                print(f"❌ STT error: {ex}")
                continue
            if not user_input:
                continue

            print(f"\n{index}:{user_input}")


           
        except KeyboardInterrupt:
            print("\n⛔ KeyboardInterrupt: stopping assistant.")
            break
        except Exception as loop_ex:
            print(f"❌ Loop error: {loop_ex}")
            traceback.print_exc()
            time.sleep(0.2)

    cleanup()
    print("✅ System stopped successfully.")


# ------------------- Entry Point -------------------
if __name__ == "__main__":
    main()
