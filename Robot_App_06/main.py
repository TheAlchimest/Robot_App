# main.py
# -------------------------------------------------------------------
# End-to-end pipeline:
#  Mic (record_until_silence WAV 16k) -> STT -> local commands -> n8n -> TTS
# Optimizations:
#  - Interrupt TTS on user speech
#  - Bounded queues to prevent lag
#  - Background threads with safe shutdown
# -------------------------------------------------------------------

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

# (Optional) eye player (disabled by default via Config)
try:
    from video_eye_player import playEyeVideo
except Exception:
    playEyeVideo = None

cfg = Config()

# Queues (bounded to prevent lag)
audio_q    = queue.Queue(maxsize=2)   # bytes (WAV16k)
text_q     = queue.Queue(maxsize=2)   # user text
response_q = queue.Queue(maxsize=2)   # assistant text

class SystemState:
    def __init__(self):
        self.active = True
        self.listening = True
        self.session_id = os.getenv("SESSION_ID", "robot-1")

    def pause(self):
        self.listening = False

    def resume(self):
        self.listening = True

state = SystemState()

rec = AudioRecorder(cfg)
stt = SpeechToText(cfg)
tts = TextToSpeech(cfg)
bot = N8nClient(cfg)

def safe_put(q: queue.Queue, item):
    try:
        if q.full():
            q.get_nowait()
        q.put_nowait(item)
    except Exception:
        pass

# -------- Threads --------

def audio_thread():
    while state.active:
        try:
            if not state.listening:
                time.sleep(0.1)
                continue

            # Interrupt any TTS immediately when user starts talking
            tts.interrupt()

            wav_bytes = rec.record_until_silence(
                silence_threshold=cfg.SILENCE_THRESHOLD,
                silence_duration=cfg.SILENCE_DURATION,
                max_duration=cfg.MAX_RECORD_SEC,
                min_duration=cfg.MIN_RECORD_SEC
            )
            if not wav_bytes:
                continue

            safe_put(audio_q, wav_bytes)
        except Exception as e:
            print(f"[Audio] error: {e}")
            time.sleep(0.2)

def stt_thread():
    while state.active:
        try:
            wav_bytes = audio_q.get(timeout=0.2)
        except queue.Empty:
            continue
        try:
            user_text = stt.transcribe_bytes(wav_bytes, is_wav=True)
            if user_text:
                safe_put(text_q, user_text)
        except Exception as e:
            print(f"[STT] error: {e}")

def ai_thread():
    while state.active:
        try:
            user_text = text_q.get(timeout=0.2)
        except queue.Empty:
            continue

        try:
            should_continue, local_resp, action, pass_text = handle_local_command(user_text)

            if action == "pause":
                state.pause()
            elif action == "resume":
                state.resume()

            if local_resp:
                safe_put(response_q, local_resp)

            if should_continue and state.listening:
                query = pass_text.strip() if pass_text else user_text
                reply = bot.chat(state.session_id, query)
                if reply:
                    safe_put(response_q, reply)

        except Exception as e:
            print(f"[AI] error: {e}")

def tts_thread():
    while state.active:
        try:
            text = response_q.get(timeout=0.2)
        except queue.Empty:
            continue
        try:
            tts.reset_interrupt()
            tts.say(text, voice=cfg.DEFAULT_VOICE)
        except Exception as e:
            print(f"[TTS] error: {e}")

def eye_thread():
    if not cfg.ENABLE_EYE_VIDEO or not playEyeVideo:
        return
    try:
        playEyeVideo()
    except Exception as e:
        print(f"[Eye] error: {e}")

# -------- Graceful shutdown --------

def shutdown(*_):
    print("\n[System] Shutting down...")
    state.active = False
    try: tts.interrupt()
    except: pass
    try: tts.cleanup()
    except: pass
    try: rec.close()
    except: pass

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

def main():
    threads = [
        threading.Thread(target=audio_thread, name="Audio", daemon=True),
        threading.Thread(target=stt_thread,   name="STT",   daemon=True),
        threading.Thread(target=ai_thread,    name="AI",    daemon=True),
        threading.Thread(target=tts_thread,   name="TTS",   daemon=True),
    ]
    if cfg.ENABLE_EYE_VIDEO and playEyeVideo:
        threads.append(threading.Thread(target=eye_thread, name="Eye", daemon=True))

    for t in threads: t.start()

    print("🤖 Ready. Say something… (Ctrl+C to exit)")
    try:
        while state.active:
            time.sleep(0.5)
    finally:
        shutdown()

if __name__ == "__main__":
    main()
