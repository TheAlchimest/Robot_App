# ==================== AI Assistant System ====================
# voice assistant (Configurable)
# Wake Word: Ziko / زيكو
# =============================================================

# ------------------- Import Libraries -------------------
from audio_recorder import AudioRecorder
from speech_to_text_windows import SpeechToText
from text_to_speech_windows import TextToSpeech
from ai_n8n import N8nClient
import pygame
import os
import re
import sys
import time
import traceback
import threading
from queue import Queue, Empty
import argparse

from Config import Config
from utilities import WakeWordDetector, StopCommandDetector
#from local_commands import LocalCommandHandler
#from local_commands import get_handler
from local_commands import LocalCommandHandler
from audio_player import AudioPlayer
eye = None

# ------------------- Environment Setup -------------------
if sys.platform.startswith("linux"):
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XAUTHORITY", "/home/pi/.Xauthority")
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# ================= System State Manager =================
class SystemState:
    """
    Thread-safe system state manager
    Handles listening state, speaking state, and interruptions
    """
    def __init__(self):
        self.is_listening = True
        self.is_active = True
        self.is_speaking = False
        self.allow_listening_to_user= False
        self.lock = threading.Lock()
    
    def pause_listening(self):
        """Pause the listening state"""
        with self.lock:
            self.is_listening = False
    
    def resume_listening(self):
        """Resume the listening state"""
        with self.lock:
            self.is_listening = True
    
    def should_listen(self):
        """Check if system should be listening"""
        with self.lock:
            return self.is_listening and self.is_active
    # interruption functions
    def pause_interruption(self):
        """Pause the interruption state"""
        with self.lock:
            self.allow_listening_to_user = False
    
    def resume_interruption(self):
        """Resume the interruption state"""
        with self.lock:
            print(F"resume_interruption")
            print(F"allow_interruption:{allow_interruption}")
            self.allow_listening_to_user = allow_interruption and True
  
    def set_speaking(self, speaking):
        """Set the speaking state"""
        with self.lock:
            self.is_speaking = speaking
    
    def get_speaking(self):
        """Get the current speaking state"""
        with self.lock:
            return self.is_speaking
    
    def stop_system(self):
        """Stop the entire system"""
        with self.lock:
            self.is_active = False

    
    def interrupt(self):
        with self.lock:
            print("\n⚠️ INTERRUPT: User is speaking - stopping all processes...")
            try:
                tts.interrupt()
            except:
                pass
            try:
                audio_player.stop_current()   # <-- مهم لإيقاف أي صوت جارٍ
                audio_player.flush_queue()    # اختياري لمسح أي أصوات انتظار
            except:
                pass
            self.clear_all_queues()           # لو عندك طوابير أخرى أضفها هنا
            self.is_speaking = False
            self.is_listening = True
            print("✅ All processes stopped, ready for new input")

    
    def clear_all_queues(self):
        """Clear all communication queues"""
        # Clear audio_queue
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except Empty:
                break

    def clear_all_queues(self):
        """Clear all communication queues"""
        for q in (audio_queue,): 
            while not q.empty():
                try: q.get_nowait()
                except Empty: break


# ------------------- Initialize Components -------------------
recorder = AudioRecorder()
stt = SpeechToText()
tts = TextToSpeech()
n8n = N8nClient()
config = Config()
# ===================== Global Variables =====================
allow_interruption = False
allow_wake_word = True
device = "raspi5"
eye_model = "img"
has_eye_model = False
# ------------------- Queues for Thread Communication -------------------
audio_queue = Queue(maxsize=3)
system_state = SystemState()
stopCommandDetector = StopCommandDetector()
wakewordDetector = WakeWordDetector()
audio_player = AudioPlayer(sample_rate=16000, channels=1, buffer=512)

#localCommandHandler = get_handler(enable_stats=True)
localCommandHandler = LocalCommandHandler(language_preference='english ', enable_stats = False)




# ------------------- Utility Methods -------------------
# ===================== Parse Command Arguments =====================
def parse_args():
    parser = argparse.ArgumentParser(description="Zico AI System Parameters")

    parser.add_argument("--allow_interruption", type=lambda v: v.lower() == "true", default=None)

    parser.add_argument("--allow_wake_word", type=lambda v: v.lower() == "true", default=None)

    parser.add_argument(
        "--device",
        type=str,
        choices=["raspi5", "raspi0", "windows"],
        help="Select device type (default from .env)"
    )
    parser.add_argument(
        "--eye_model",
        type=str,
        choices=["img", "video", "drawing", "none"],
        help="Select eye model type (default from .env)"
    )

    return parser.parse_args()


def speak_safe(text: str):
    """Speak safely with basic interruption handling."""
    if not text:
        return
    try:
        tts.interrupt()
    except Exception:
        pass
    try:
        tts.say(text)
    except Exception as ex:
        print(f"❌ Speech error: {ex}")


def safe_put(q, item):
    try:
        q.put_nowait(item)
    except:
        try: q.get_nowait()  # drop oldest
        except Empty: pass
        q.put_nowait(item)
# ------------------- Utility Methods END-------------------
# ===================== Initialize Global Settings =====================
def initialize_settings():
    global allow_interruption, allow_wake_word, device, eye_model, has_eye_model, eye

    args = parse_args()

    allow_interruption = (args.allow_interruption if args.allow_interruption is not None else config.ALLOW_INTERRUPTION)
    allow_wake_word = (args.allow_wake_word if args.allow_wake_word is not None else config.ALLOW_WAKE_WORD )

    device = args.device or config.DEVICE
    eye_model = args.eye_model or config.EYE_MODEL

    # Normalize "none" values and detect if model exists
    if eye_model is None or str(eye_model).lower() == "none":
        has_eye_model = False
        eye = None
    else:
        has_eye_model = True

        # Dynamic import based on eye_model value
        if eye_model == "drawing":
            import eye_runner_zero as eye
        elif eye_model == "img":
            import eye_runner as eye
        elif eye_model == "video":
            import eye_video_player as eye
        else:
            print(f"⚠️ Unknown eye_model '{eye_model}', skipping eye initialization.")
            eye = None
            has_eye_model = False

    # Print configuration summary
    print("\n========= CONFIGURATION =========")
    print(f"allow_interruption = {allow_interruption}")
    print(f"allow_wake_word    = {allow_wake_word}")
    print(f"device             = {device}")
    print(f"eye_model          = {eye_model}")
    print(f"has_eye_model      = {has_eye_model}")
    print("=================================\n")

# ===================== ========================= =====================

def cleanup():
    """Cleanup resources gracefully."""
    '''
    try:
        eye.cleanup()
    except Exception:
        pass
    '''
    try:
        recorder.close()
    except Exception:
        pass
    try:
        tts.interrupt()
        tts.cleanup()
    except Exception:
        pass
    try:
        stt.cleanup()
    except Exception:
        pass

    audio_player.shutdown()
    





def interruption_thread():
    """
    Always-on short-window listener for 'stop' (with/without wake word).
    - Records tiny windows (~1.0–1.5s) to detect "stop"/"توقف" even while speaking or waiting for AI.
    - If detected, triggers SystemState.interrupt() immediately and plays a short 'cancelled' chime.
    - Keeps CPU usage reasonable by sleeping briefly between empty windows.
    """
    while system_state.is_active:
        if system_state.allow_listening_to_user:
            try:
                # Small capture window: fast turnaround and low latency.
                audio_buf = recorder.record_until_silence(
                    max_duration=1.3,          # small window (tune 1.0–1.5s)
                    noise_calib_duration=0.0,  # no calibration per window to keep latency low
                    start_frames=2,
                    end_frames=8,
                    post_silence_hold=0.0,
                    pre_roll_ms=200,
                    min_speech_after_start=0.2,
                    threshold_boost=0.0
                )
                if not audio_buf:
                    # No voice activity detected in this small window.
                    time.sleep(0.05)
                    continue

                # Transcribe the small window. Use the same STT engine.
                try:
                    partial = stt.transcribe_bytes(audio_buf)
                except Exception:
                    # If STT fails for a tiny chunk, just skip silently.
                    continue

                if not partial:
                    continue

                # If user said a stop command (with/without wake), interrupt immediately.
                if stopCommandDetector.is_stop_with_optional_wake(partial):
                    system_state.interrupt()
                    print("🛑 BARGE-IN: stop detected (with/without wake).")
                    #audio_player.play_blocking("Resources/voice_msgs/cancelled.wav")
                    audio_player.play_blocking("Resources/voice_msgs/listening.wav")
                    system_state.resume_listening()
                    # Small back-off to avoid retriggering on the same audio chunk.
                    time.sleep(0.3)

            except Exception:
                # Soft-fail to keep the barge-in listener robust.
                time.sleep(0.1)

# ------------------- Main Function -------------------
def main_thread():
    # pygame.init()

    print("="*60)
    print("🚀 AI Assistant Started — Wake Word: Ziko / زيكو")
    print("="*60)
    print("Say 'Ziko ...' or 'زيكو ...' to issue a command.")
    print("Say 'stop' or 'توقف' anytime to cancel.")
    print("="*60)

    audio_player.play_blocking("Resources/voice_msgs/zico_welcome.wav")

    listening = True
    last_status = time.time()
    is_first_time=True
    while system_state.is_active:
        try:
            system_state.pause_interruption()
            
            if not is_first_time:
                audio_player.play_blocking("Resources/voice_msgs/bell.wav")
                #print("ℹ️ Listening..." if listening else "⏸️ Paused. Say 'wake up' to resume.")
            is_first_time = False
            if not listening:
                print("❌ not listening")
                time.sleep(0.1)
                continue

            print("ℹ️ Listening...")
            # 1) Record
            audio_buffer = recorder.record_until_silence(
                max_duration=25.0,
                noise_calib_duration=0.8,
                start_frames=3,
                end_frames=18,            # جَرّب 18-22 لو لسه بيقطع
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

            print(f"\n🎤 User: {user_input}")

            # 3) Safety stop (works without wake word)
            if stopCommandDetector.is_stop_command(user_input):
                try:
                    system_state.interrupt()
                except Exception:
                    pass
                print("⚠️ Stop command detected, cancelled speech.")
                continue
            user_message = user_input        
            if allow_wake_word:
                # 4) Enforce wake word (Ziko/زيكو variants)
                has_wake, remaining, wake_form = wakewordDetector.extract_after_wake(user_message)
                if not has_wake:
                    print("⏭️ Ignored (no wake word).")
                    # اختياري: تشغيل نغمة خفيفة تدل إن النظام لم يلتقط نداء زيكو
                    # audio_player.play_blocking("Resources/voice_msgs/need_wake.wav")
                    continue
                else:
                    user_message = remaining

            print(F"⏭️ user_message:{user_message}.")

            # لو النداء فقط بدون أمر
            if not user_message:
                audio_player.play_blocking("Resources/voice_msgs/yes_how_help.wav")
                continue

            # 5) Local commands THEN AI (using the remainder only)
            try:
                should_continue, local_response, action, pass_text = localCommandHandler.handle(user_message)
                print(f"should_continue:{should_continue} / local_response:{local_response} / action:{action}")
            except Exception as ex:
                print(f"❌ Local command error: {ex}")
                traceback.print_exc()
                should_continue, local_response, action, pass_text = True, None, None, user_message
            '''
            if action == 'pause':
                listening = False
                print("💤 System paused.")
            elif action == 'resume':
                listening = True
                print("✅ System resumed.")
                '''

            if local_response:
                print(f"🤖 Local Response: {local_response}")
                speak_safe(local_response)

            if should_continue and listening:
                try:
                    system_state.resume_interruption()
                    # tell user that we are thinking now untill we got response from AI 
                    # audio_player.play_blocking("Resources/voice_msgs/thinking.wav")
                    audio_player.play_async("Resources/voice_msgs/thinking.wav")
                    print("🤔 Processing with AI...")

                    # NOTE: pass_text (if greetings trimmed) else remainder
                    prompt_text = pass_text if pass_text else user_message
                    ai_response = n8n.chat("123456", prompt_text)
                    if ai_response:
                        print(f"🤖 AI Response: {ai_response}")
                        # tell user that we got answer untill we convert the AI response into sound
                        # audio_player.play_blocking("Resources/voice_msgs/got_it.wav")
                        audio_player.play_async("Resources/voice_msgs/got_it.wav")
                        # convert the AI response into sound
                        speak_safe(ai_response)
            
                    system_state.pause_interruption()
                except Exception as ex:
                    print(f"❌ AI error: {ex}")
                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n⛔ KeyboardInterrupt: stopping assistant.")
            break
        except Exception as loop_ex:
            print(f"❌ Loop error: {loop_ex}")
            traceback.print_exc()
            time.sleep(0.2)

    cleanup()
    print("✅ System stopped successfully.")


# ================= Main Function =================
def main():

    initialize_settings()
    audio_player.start()


    # Create and start threads
    threads = []

    # 🧩 Add interruption thread only if enabled
    if allow_interruption:
        threads.append(
            threading.Thread(target=interruption_thread, daemon=True, name="InterruptionThread")
        )
    else:
        print("⚠️ Interruption disabled, skipping InterruptionThread")

    # 👁️ Add eye thread only if eye_model is not None
    if has_eye_model and eye is not None:
        threads.append(threading.Thread(target=eye.run, daemon=True, name="EyeThread"))
    else:
        print("⚠️ No eye model loaded, skipping EyeThread")


    # 🧠 Always run main logic thread
    threads.append(
        threading.Thread(target=main_thread, daemon=True, name="MainThread")
    )

    # Start all threads
    for thread in threads:
        thread.start()
        print(f"✅ Started: {thread.name}")

    print("\n" + "=" * 60)
    print("✅ System ready! Start with 'Zico ...' or 'زيكو ...'")
    print("=" * 60 + "\n")

    # Keep main thread alive
    try:
        while system_state.is_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⛔ Shutting down system...")
        system_state.stop_system()
        cleanup()
        

        # tracker.closeAllWindows()
        
        print("✅ System stopped successfully")
        print("=" * 60)

# ------------------- Entry Point -------------------
if __name__ == "__main__":
    main()
