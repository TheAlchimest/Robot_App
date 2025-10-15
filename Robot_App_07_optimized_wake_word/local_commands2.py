# local_commands.py
# -------------------------------------------------------------------
# Local commands handler and wake-word detection for "Ziko / زيكو"
# -------------------------------------------------------------------

import re
from typing import Tuple

GREETING_AR = ["مرحبا", "اهلا", "أهلا", "السلام عليكم", "هلا", "اهلين", "صباح الخير", "مساء الخير"]
GREETING_EN = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy"]

def _contains_any(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w.lower() in t for w in words)

# ---------------- Arabic normalization ----------------
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

def normalize_en(text: str) -> str:
    # تخفيف علامات وترقيم ونقط متكررة وتطبيع بسيط
    t = (text or "").strip().lower()
    t = re.sub(r"[\"'`~^]", "", t)
    t = re.sub(r"\.{2,}", ".", t)  # تقليل سلاسل النقاط
    return t

# ---------------- Wake-word candidates ----------------
# إنجليزي: البدائل المقصودة + أخطاء STT القريبة (بدون "zika"!)
_EN_EXACT_ALLOWED = {
    "ziko", "zico", "zeeko", "zeeco",  # لفظ/مد صوتي
    "dico", "dziko",                   # التباس Z/D (صوتيًا)
}

# كلمات ينبغي رفضها صراحةً حتى لو قريبة شكليًا
_EN_DENY = {
    "zika", "nico", "nika", "niko", "nikaa"
}

# عربي: زيكو مع/بدون "يا"
_AR_WAKE_REGEX = re.compile(r"^\s*(?:يا\s*)?زيكو\b[\s،,:-]*", re.IGNORECASE)

# تحيات (اختيارية) قبل الويك وورد
_EN_VOC = r"(?:hey|hi|hello)\s+"

# نسخة إنجليزية من الويك وورد (مع التحية اختيارية)
_EN_WAKE_REGEX = re.compile(
    rf"^\s*(?:{_EN_VOC})?([a-z\.!,?:;]+)\b[\s,،:-]*",  # نلتقط أول توكن حروف/نقاط/علامات شائعة
    re.IGNORECASE
)

_PUNCT_TAIL = re.compile(r"[\.!,?:;]+$")  # لإزالة علامات الوقف من آخر التوكن

def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        # أبعد من المطلوب
        return 3
    la, lb = len(a), len(b)
    dp = [[0]*(lb+1) for _ in range(la+1)]
    for i in range(la+1): dp[i][0] = i
    for j in range(lb+1): dp[0][j] = j
    for i in range(1, la+1):
        for j in range(1, lb+1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
    return dp[-1][-1]

def _is_english_wake_token(tok: str) -> bool:
    if not tok:
        return False

    t = tok.lower().strip()
    t = _PUNCT_TAIL.sub("", t)  # ziko. -> ziko

    # رفض مبكر للكلمات المضللة الشائعة
    if t in _EN_DENY:
        return False

    # قبول مطابقات صريحة
    if t in _EN_EXACT_ALLOWED:
        return True

    # شروط عامة للتجويز
    if not t or t[0] not in {"z", "d"}:
        return False
    if not (3 <= len(t) <= 5):
        return False
    if t == "z":  # حالات حرف مفرد
        return False

    # سماح بمسافة تحرير بسيطة مع الصيغ المعروفة
    return (_lev(t, "ziko") <= 1) or (_lev(t, "zico") <= 1)

def extract_after_wake(user_text: str) -> Tuple[bool, str, str]:
    """
    Returns (has_wake: bool, remainder: str, wake_form: str)
    - Detects 'Ziko' variants in EN (with optional 'hey/hi/hello' before it),
      and 'زيكو' (with optional 'يا') in AR.
    - Only detects at the BEGINNING of the text.
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", ""

    # ----- Try English path -----
    t_en = normalize_en(text)
    m_en = _EN_WAKE_REGEX.match(t_en)
    if m_en:
        first_token = (m_en.group(1) or "").lower()
        if _is_english_wake_token(first_token):
            return True, text[m_en.end():].strip(), first_token

    # ----- Try Arabic path (on normalized AR) -----
    norm_ar = normalize_ar(text)
    m_ar = _AR_WAKE_REGEX.match(norm_ar)
    if m_ar:
        # قصّ نفس الجزء من النص الأصلي قدر الإمكان
        m_orig = re.match(r"^\s*(?:يا\s*)?زيكو\b[\s،,:-]*", text, re.IGNORECASE)
        end_idx = m_orig.end() if m_orig else len(text)
        wf = (m_orig.group(0).strip() if m_orig else "زيكو")
        return True, text[end_idx:].strip(), wf

    return False, "", ""

# ---------------- Core Local Commands ----------------

def handle_local_command(user_text: str):
    """
    Returns tuple:
      (should_continue_to_ai: bool, local_response: str, action: str|None, pass_text: str)

    Logic:
      - If greeting AND other content => short local reply + pass remainder to AI.
      - If pure greeting => only local reply (no AI).
      - Else: pass through to AI.
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", None, ""

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


# ================= Entry Point (quick tests) =================
if __name__ == "__main__":
    tests = [
        "Ziko play some music",                # ✅ wake
        "hey zico open mail",                  # ✅ wake
        "Dico what's the weather",             # ✅ wake (التباس D/Z مسموح)
        "Dziko, read my latest email",         # ✅ wake
        "Nico open calendar",                  # ❌ no wake
        "Zika is a virus",                     # ❌ no wake (deny-list)
        "Z.",                                  # ❌ no wake
        "Z",                                   # ❌ no wake
        "زيكو: ابحث عن الأخبار",               # ✅ wake
        "يا زيكو افتح البريد",                  # ✅ wake
        "hello ziko, what's up?",              # ✅ wake
        "sorry, ziko open mail",               # ❌ no wake (ليس في بداية النص)
        "ZEeCo, open settings",                # ✅ wake (zeeco ~ zico)
    ]
    for s in tests:
        print(s, "=>", extract_after_wake(s))
