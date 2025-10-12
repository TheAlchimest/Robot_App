# local_commands.py
# -------------------------------------------------------------------
# Lightweight local intent for greetings, pause/resume, and quick replies.
# Supports "greeting + question" by returning pass_text to the AI.
# -------------------------------------------------------------------

import re

GREETING_AR = ["مرحبا", "اهلا", "أهلا", "السلام عليكم", "هلا", "اهلين", "صباح الخير", "مساء الخير"]
GREETING_EN = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy"]

PAUSE_WORDS  = ["توقف", "اسكت", "اهدأ", "pause", "stop", "mute"]
RESUME_WORDS = ["اسمع", "تابع", "استمع", "resume", "continue", "listen"]

def _contains_any(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w.lower() in t for w in words)

def handle_local_command(user_text: str):
    """
    Returns tuple:
      (should_continue_to_ai: bool, local_response: str, action: str|None, pass_text: str)

    Logic:
      - If pause/resume, act locally (no AI).
      - If greeting AND other content => short local reply + pass remainder to AI.
      - If pure greeting => only local reply (no AI).
      - Else: pass through to AI.
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", None, ""

    # Pause / Resume
    if _contains_any(text, PAUSE_WORDS):
        return False, "تم الإيقاف مؤقتًا. قل 'استمع' للمتابعة.", "pause", ""
    if _contains_any(text, RESUME_WORDS):
        return False, "تم الاستئناف. أنا معك.", "resume", ""

    # Greetings
    is_greet = any(g.lower() in text.lower() for g in GREETING_AR + GREETING_EN)
    if is_greet:
        # احذف التحية من بداية النص إن وُجدت لتستخرج السؤال الحقيقي
        pat = r"^\s*(?:%s)[\s،,:-]*" % ("|".join(map(re.escape, GREETING_AR + GREETING_EN)))
        pass_text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
        local_resp = "أهلاً! تحت أمرك."
        if pass_text:
            return True, local_resp, None, pass_text
        else:
            return False, local_resp, None, ""

    # No local action
    return True, "", None, text
