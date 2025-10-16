# main_with_eyes.py
# النسخة المحسّنة من main.py مع دعم العيون المتحركة

import os
import time
import queue
import signal
import threading

from Config import Config
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech
from ai_n8n import N8nClient
from local_commands import handle_local_command

# ✅ استيراد وحدة العيون
try:
    from face_tracker import run_eyes_threaded, eye_state
    HAS_EYES = True
except ImportError:
    HAS_EYES = False
    print("⚠️  Eye tracking not available (face_tracker.py missing)")

cfg = Config()

# Queues
audio_q = queue.Queue(maxsize=5)
text_q = queue.Queue(maxsize=5)
response_q = queue.Queue(maxsize=5)

# Events
new_audio_event = threading.Event()
new_text_event = threading.Event()
new_response_event = threading.Event()
shutdown_event = threading.Event()

class SystemState:
    def __init__(self):
        self.active = True
        self.listening = True
        self.session_id = os.getenv("SESSION_ID", "robot-1")
        self._lock = threading.Lock()

    def pause(self):
        with self._lock:
            self.listening = False
            print("[State] 🔇 Listening paused")

    def resume(self):
        with self._lock:
            self.listening = True
            print("[State] 🔊 Listening resumed")

    def is_listening(self):
        with self._lock:
            return self.listening

state = SystemState()

rec = AudioRecorder(cfg)
stt = SpeechToText(cfg)
tts = TextToSpeech(cfg)
bot = N8nClient(cfg)

def safe_put(q: queue.Queue, item, event: threading.Event):
    try:
        q.put(item, timeout=0.5)
        event.set()
        return True
    except queue.Full:
        print(f"[Queue] ⚠️ Queue full")
        try:
            q.get_nowait()
            q.put_nowait(item)
            event.set()
            return True
        except Exception:
            return False

# ========== THREADS ==========

def audio_thread():
    print("[Audio] 🎤 Started")
    
    while not shutdown_event.is_set():
        try:
            if not state.is_listening():
                time.sleep(0.1)
                continue

            wav_bytes = rec.record_until_silence(
                silence_threshold=cfg.SILENCE_THRESHOLD,
                silence_duration=cfg.SILENCE_DURATION,
                max_duration=cfg.MAX_RECORD_SEC,
                min_duration=cfg.MIN_RECORD_SEC
            )
            
            if not wav_bytes or len(wav_bytes) < 1000:
                print(F"len(wav_bytes):{len(wav_bytes)}")
                continue

            print(F"len(wav_bytes):{len(wav_bytes)}")
            print("[Audio] 🛑 X User speaking, interrupting TTS")
            tts.interrupt()
            
            # ✅ إشارة للعيون: المستخدم يتكلم
            if HAS_EYES:
                eye_state.set_talking(False)

            safe_put(audio_q, wav_bytes, new_audio_event)

        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[Audio] ❌ Error: {e}")
                time.sleep(0.2)

def stt_thread():
    print("[STT] 📝 Started")
    
    while not shutdown_event.is_set():
        new_audio_event.wait(timeout=0.5)
        new_audio_event.clear()

        try:
            wav_bytes = audio_q.get_nowait()
        except queue.Empty:
            continue

        try:
            print("[STT] 🔄 Transcribing...")
            start_time = time.time()
            
            user_text = stt.transcribe_bytes(wav_bytes, is_wav=True)
            
            elapsed = time.time() - start_time
            print(f"[STT] ✅ Done in {elapsed:.2f}s: '{user_text}'")
            
            if user_text:
                safe_put(text_q, user_text, new_text_event)
                
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[STT] ❌ Error: {e}")

def ai_thread():
    print("[AI] 🤖 Started")
    
    while not shutdown_event.is_set():
        new_text_event.wait(timeout=0.5)
        new_text_event.clear()

        try:
            user_text = text_q.get_nowait()
        except queue.Empty:
            continue

        try:
            print(f"[AI] 💬 Processing: '{user_text}'")
            
            should_continue, local_resp, action, pass_text = handle_local_command(user_text)

            if action == "pause":
                state.pause()
            elif action == "resume":
                state.resume()

            if local_resp:
                safe_put(response_q, local_resp, new_response_event)

            if should_continue and state.is_listening():
                query = pass_text.strip() if pass_text else user_text
                
                start_time = time.time()
                reply = bot.chat(state.session_id, query)
                elapsed = time.time() - start_time
                
                print(f"[AI] ✅ Got response in {elapsed:.2f}s")
                
                if reply:
                    safe_put(response_q, reply, new_response_event)

        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[AI] ❌ Error: {e}")

def tts_thread():
    print("[TTS] 🔊 Started")
    
    while not shutdown_event.is_set():
        new_response_event.wait(timeout=0.5)
        new_response_event.clear()

        try:
            text = response_q.get_nowait()
        except queue.Empty:
            continue

        try:
            print(f"[TTS] 🗣️ Speaking: '{text[:50]}...'")
            
            # ✅ إشارة للعيون: الروبوت يتكلم
            if HAS_EYES:
                eye_state.set_talking(True)
            
            tts.reset_interrupt()
            start_time = time.time()
            
            tts.say(text, voice=cfg.DEFAULT_VOICE)
            
            elapsed = time.time() - start_time
            print(f"[TTS] ✅ Done in {elapsed:.2f}s")
            
            # ✅ إشارة للعيون: انتهى الكلام
            if HAS_EYES:
                eye_state.set_talking(False)
            
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[TTS] ❌ Error: {e}")
            # تأكد من إعادة تعيين حالة الكلام
            if HAS_EYES:
                eye_state.set_talking(False)

def eyes_thread():
    """Thread لتشغيل العيون"""
    if not HAS_EYES:
        return
    
    print("[Eyes] 👁️ Started")
    
    # اختر الوضع من Config
    eye_mode = os.getenv("EYE_MODE", "natural")  # "natural" أو "tracking"
    enable_arduino = os.getenv("ENABLE_ARDUINO", "0") in ("1", "true", "yes")
    
    try:
        run_eyes_threaded(mode=eye_mode, enable_arduino=enable_arduino)
    except Exception as e:
        print(f"[Eyes] ❌ Error: {e}")

# ========== SHUTDOWN ==========

def shutdown(*_):
    print("\n[System] 🛑 Shutting down...")
    shutdown_event.set()
    
    new_audio_event.set()
    new_text_event.set()
    new_response_event.set()
    
    # إيقاف العيون
    if HAS_EYES:
        eye_state.stop()
    
    try:
        tts.interrupt()
        tts.cleanup()
    except Exception:
        pass
    
    try:
        rec.close()
    except Exception:
        pass
    
    try:
        stt.cleanup()
    except Exception:
        pass
    
    print("[System] ✅ Cleanup complete")

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ========== MAIN ==========

def main():
    print("=" * 60)
    print("🤖 AI ROBOT - WITH ANIMATED EYES")
    print("=" * 60)
    print(f"Session ID: {state.session_id}")
    print(f"Voice: {cfg.DEFAULT_VOICE}")
    
    if HAS_EYES:
        eye_mode = os.getenv("EYE_MODE", "natural")
        print(f"Eyes Mode: {eye_mode}")
        print("👁️  Eyes enabled")
    else:
        print("👁️  Eyes disabled (module not found)")
    
    print("=" * 60)
    
    threads = [
        threading.Thread(target=audio_thread, name="Audio", daemon=True),
        threading.Thread(target=stt_thread, name="STT", daemon=True),
        threading.Thread(target=ai_thread, name="AI", daemon=True),
        threading.Thread(target=tts_thread, name="TTS", daemon=True),
    ]
    
    # ✅ إضافة thread العيون إذا كان متاحاً
    if HAS_EYES:
        threads.append(threading.Thread(target=eyes_thread, name="Eyes", daemon=True))

    for t in threads:
        t.start()

    print("\n✅ System ready! Say something... (Ctrl+C to exit)\n")
    
    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1.0)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()
        
        for t in threads:
            t.join(timeout=2.0)

if __name__ == "__main__":
    main()