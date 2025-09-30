# text_to_speech/elevenlabs_text_to_speech.py

import os
import tempfile
import pygame
from typing import Literal
from elevenlabs.client import ElevenLabs
from Config import Config

config = Config()

# أنشئ الـ client بمفتاحك
elevenlabs = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

# أشهر الأصوات في ElevenLabs (يمكنك الحصول على القائمة الكاملة من API)
VOICE_IDS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "drew": "29vD33N1CtxCmqQRPOHJ", 
    "clyde": "2EiwWnXFnvU5JabPnv8n",
    "paul": "5Q0t7uMcjvnagumLfvZi",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    "dave": "CYw3kZ02Hs0563khs1Fj",
    "fin": "D38z5RcWu1voky8WS1ja",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "thomas": "GBv7mTt0atIp3Br8iCZE",
    "emily": "LcfcDJNUP1GQjkzn1xUU",
    "elli": "MF3mGyEYCl7XYWbV9V6O",
    "callum": "N2lVS1w4EtoT3dr4eOWO",
    "patrick": "ODq5zmih8GrVes37Dizd",
    "harry": "SOYHLrjzK2X1ezoPC6cr",
    "liam": "TX3LPaxmHKxFdv7VOQHJ",
    "dorothy": "ThT5KcBeYPX3keUQqHPh",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "arnold": "VR6AewLTigWG4xSOukaG",
    "charlotte": "XB0fDUnXU5powFXDhCwa",
    "matilda": "XrExE9yKIg1WjnnlVkGX",
    "james": "ZQe5CZNOzWyzPSCn5a3c",
    "joseph": "Zlb1dXrM653N07WRdFW3",
    "jeremy": "bVMeCyTHy58xNoL34h3p",
    "michael": "flq6f7yk4E4fJM5XTYuZ",
    "ethan": "g5CIjZEefAph4nQFvHAz",
    "gigi": "jBpfuIE2acCO8z3wKNLl",
    "freya": "jsCqWAovK2LkecY7zXl4",
    "brian": "nPczCjzI2devNBz1zQrb",
    "grace": "oWAxZDx7w5VEj9dCyTzz",
    "daniel": "onwK4e9ZLuTAKqWW03F9"
}

def play_file_with_pygame(file_path: str) -> None:
    """يشغّل ملف صوت (mp3/wav) باستخدام pygame ثم ينتظر لحدّ ما يخلص."""
    # مبدئيًا نعمل init مرة واحدة
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    # انتظر لحد ما ينتهي التشغيل
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        clock.tick(10)

def text_to_speech(text: str) -> None:
    """
    يحوّل نص إلى كلام باستخدام ElevenLabs ثم يشغّله عبر pygame بدون الحاجة إلى ffplay.
    """
    # اختَر أحد هذه المخرجات (MP3 أو WAV). MP3 غالبًا أسهل على ويندوز.
    use_wav = False  # غيّرها إلى True لو عايز WAV

    output_format: Literal[
        "mp3_44100_128",
        "mp3_44100_64",
        "mp3_22050_32",
        "pcm_16000",           # RAW PCM (بدون رأس WAV)
        "wav_44100_16"         # WAV 44.1kHz 16-bit (لو مدعوم في نسختك من الـ SDK)
    ]

    if use_wav:
        output_format = "wav_44100_16"  # لو أعطاك خطأ، جرّب "mp3_44100_128" وخلّي use_wav=False
        suffix = ".wav"
    else:
        output_format = "mp3_44100_128"
        suffix = ".mp3"

    # NOTE: convert() بيرجع generator of bytes (chunks)
    audio_chunks = elevenlabs.text_to_speech.convert(
        text=text,                               # استخدم النص اللي مرّرته
        #voice_id="JBFqnCBsd6RMkjVDRZzb",         # غيّر الصوت حسب رغبتك
        voice_id=VOICE_IDS["rachel"],
        model_id="eleven_multilingual_v2",
        output_format=output_format,
    )

    # اجمع ال-chunks إلى بايتات واحدة
    audio_bytes = b"".join(chunk for chunk in audio_chunks)

    # اكتب لملف مؤقّت بالامتداد المناسب؛ pygame يحب المسار الفعلي أكثر من BytesIO
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        play_file_with_pygame(tmp_path)
    finally:
        # نظّف الملف المؤقت
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except PermissionError:
                # لو لسه المشغّل ماسك الملف لحظة، تجاهل التنظيف بصمت
                pass

if __name__ == "__main__":
    text_to_speech("صباح الخير")
