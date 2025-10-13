# local_commands.py
# -------------------------------------------------------------------
# Local commands handler and wake-word detection for "Ziko / زيكو"
# -------------------------------------------------------------------

import re

GREETING_AR = ["مرحبا", "اهلا", "أهلا", "السلام عليكم", "هلا", "اهلين", "صباح الخير", "مساء الخير"]
GREETING_EN = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy"]

PAUSE_WORDS  = ["توقف", "اسكت", "اهدأ", "pause", "stop", "mute"]
RESUME_WORDS = ["اسمع", "تابع", "استمع", "resume", "continue", "listen"]

def _contains_any(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w.lower() in t for w in words)

# ---------------- Wake-word helpers (Ziko) ----------------

# Arabic normalization (lightweight)
_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def normalize_ar(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = _AR_DIACRITICS.sub('', text)
    text = text.replace('ـ', '')
    for src in 'أإآٱ':
        text = text.replace(src, 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    return text

# Accepted wake variants
_EN_WAKE = r"(?:ziko|zeeko|zeeco|zico)"
_AR_WAKE = r"(?:زيكو|يا\s*زيكو)"

# Optional starters like "hey"/"يا"
_EN_VOC = r"(?:hey|hi|hello)\s+"
_AR_VOC = r"(?:يا)\s*"

# Build patterns (start-of-utterance only)
WAKE_PATTERN_EN = re.compile(rf"^\s*(?:{_EN_VOC})?{_EN_WAKE}\b[\s،,:-]*", re.IGNORECASE)
# نطبع بنسخة طبيعية ثم نطابق العربية على النصّ المُطبّع
WAKE_PATTERN_AR = re.compile(rf"^\s*(?:{_AR_VOC})?سولي\b[\s،,:-]*", re.IGNORECASE)

def extract_after_wake(user_text: str):
    """
    Returns (has_wake: bool, remainder: str, wake_form: str)
    - Detects 'Soly' variants in EN, and 'سولي' (with optional 'يا') in AR.
    - Only detects at the BEGINNING of the text.
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", ""

    # Try English wake
    m_en = WAKE_PATTERN_EN.match(text)
    if m_en:
        return True, text[m_en.end():].strip(), m_en.group(0).strip()

    # Try Arabic on normalized text, but we need to map back to original slicing.
    norm = normalize_ar(text)
    m_ar = WAKE_PATTERN_AR.match(norm)
    if m_ar:
        # Approximate slicing by applying same regex on original with flexible chars
        # Accept forms: "يا سولي", "سولي"
        m_orig = re.match(r"^\s*(?:يا\s*)?زيكو\b[\s،,:-]*", text, re.IGNORECASE)
        end_idx = m_orig.end() if m_orig else len(text)
        return True, text[end_idx:].strip(), (m_orig.group(0).strip() if m_orig else "سولي")

    return False, "", ""

# ---------------- Core Local Commands ----------------

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


# ================= Entry Point =================
if __name__ == "__main__":
    print(extract_after_wake("Ziko play some music"))
    print(extract_after_wake("يا زيكو افتح البريد"))
    print(handle_local_command("get me a story."))
