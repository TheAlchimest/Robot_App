# local_commands_ultra_fast.py
# -------------------------------------------------------------------
# Ultra-optimized for Raspberry Pi Zero - NO Levenshtein!
# -------------------------------------------------------------------

import re
from typing import Tuple

GREETING_AR = ["مرحبا", "اهلا", "أهلا", "السلام عليكم", "هلا", "اهلين", "صباح الخير", "مساء الخير"]
GREETING_EN = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy"]

def _contains_any(text: str, words: list[str]) -> bool:
    """فحص سريع - O(n)"""
    t = text.lower()
    return any(w in t for w in words)

# ============ Pre-compiled Regex (مرة واحدة فقط) ============
_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
_AR_WAKE_REGEX = re.compile(r"^\s*(?:يا\s*)?زيكو\b[\s،,:-]*", re.IGNORECASE)

# English: نلتقط أول كلمة فقط (بدون تعقيد)
_EN_WAKE_REGEX = re.compile(
    r"^\s*(?:hey|hi|hello\s+)?([a-z]+)[\s,،:.\-!?]*",
    re.IGNORECASE
)

# ============ Fast Lookup Sets (frozenset = أسرع) ============
# البدائل المقبولة - تطابق دقيق فقط (NO Levenshtein!)
_EN_WAKE_EXACT = frozenset({
    "ziko", "zico", "zeeko", "zeeco",
    "dico", "dziko",
    "zikko", "zeiko", "zyko", "zeko",
})

# قائمة الرفض الصريح (أولوية للسرعة)
_EN_WAKE_DENY = frozenset({
    "zika", "nico", "nika", "niko", "nikaa",
    "z", "d",  # حروف مفردة
})

# ============ Arabic Normalization (مبسّطة للغاية) ============
def normalize_ar(text: str) -> str:
    """تطبيع عربي - أسرع نسخة ممكنة"""
    if not text:
        return ""
    # إزالة التشكيل فقط (أهم خطوة)
    text = _AR_DIACRITICS.sub('', text.strip().lower())
    # تطبيع بسيط (بدون حلقات)
    text = text.translate(str.maketrans({
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
        'ة': 'ه', 'ى': 'ي', 'ـ': ''
    }))
    return text

# ============ Wake-word Detection (Ultra Fast) ============
def _is_english_wake_token(tok: str) -> bool:
    """
    فحص سريع جداً - O(1) lookup فقط، NO Levenshtein!
    """
    if not tok or len(tok) < 2:
        return False
    
    t = tok.lower()
    
    # 1. رفض فوري (أسرع خطوة)
    if t in _EN_WAKE_DENY:
        return False
    
    # 2. قبول دقيق (frozenset lookup = O(1))
    if t in _EN_WAKE_EXACT:
        return True
    
    # 3. شروط بسيطة للتوسع (بدون Levenshtein)
    # يجب أن يبدأ بـ z أو d
    if t[0] not in ('z', 'd'):
        return False
    
    # يجب أن يحتوي على "iko" أو "ico" في الوسط/النهاية
    if "iko" in t or "ico" in t:
        return True
    
    return False

def extract_after_wake(user_text: str) -> Tuple[bool, str, str]:
    """
    استخراج wake-word - محسّن للأداء الأقصى
    Returns: (has_wake, remainder, wake_form)
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", ""
    
    # ===== English Detection (Fast Path) =====
    # نعمل lowercase مرة واحدة فقط
    text_lower = text.lower()
    m_en = _EN_WAKE_REGEX.match(text_lower)
    
    if m_en:
        first_token = m_en.group(1)
        if _is_english_wake_token(first_token):
            # نستخدم النص الأصلي للقطع (ليس lowercase)
            return True, text[m_en.end():].strip(), first_token
    
    # ===== Arabic Detection =====
    # نطبّع فقط إذا لم نجد إنجليزي
    norm_ar = normalize_ar(text)
    m_ar = _AR_WAKE_REGEX.match(norm_ar)
    
    if m_ar:
        # قطع من النص الأصلي
        m_orig = re.match(r"^\s*(?:يا\s*)?زيكو\b[\s،,:-]*", text, re.IGNORECASE)
        if m_orig:
            return True, text[m_orig.end():].strip(), m_orig.group(0).strip()
        # fallback
        return True, text[5:].strip(), "زيكو"
    
    return False, "", ""

# ============ Local Commands Handler ============
def handle_local_command(user_text: str) -> Tuple[bool, str, str, str]:
    """
    معالجة الأوامر المحلية (greetings)
    Returns: (should_continue_to_ai, local_response, action, pass_text)
    """
    text = (user_text or "").strip()
    if not text:
        return False, "", "", ""
    
    # Greetings
    text_lower = text.lower()
    has_greeting = any(g in text_lower for g in GREETING_AR + GREETING_EN)
    
    if has_greeting:
        # احذف التحية من البداية
        pattern = r"^\s*(?:%s)[\s،,:-]*" % "|".join(
            re.escape(g) for g in GREETING_AR + GREETING_EN
        )
        remaining = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        
        if remaining:
            # تحية + أمر
            return True, "أهلاً! تحت أمرك.", "", remaining
        else:
            # تحية فقط
            return False, "أهلاً! تحت أمرك.", "", ""
    
    # No local action
    return True, "", "", text


# ================= Performance Testing =================
if __name__ == "__main__":
    import time
    
    print("=" * 70)
    print("🚀 ULTRA-FAST Wake-word Detection for Raspberry Pi Zero")
    print("=" * 70)
    print()
    
    test_cases = [
        # Expected to WAKE ✅
        ("Ziko play some music", True, "play some music"),
        ("hey zico open mail", True, "open mail"),
        ("Dico what's the weather", True, "what's the weather"),
        ("Dziko, read my latest email", True, "read my latest email"),
        ("hello ziko, what's up?", True, "what's up?"),
        ("ZEeCo, open settings", True, "open settings"),
        ("زيكو: ابحث عن الأخبار", True, "ابحث عن الأخبار"),
        ("يا زيكو افتح البريد", True, "افتح البريد"),
        ("ziko", True, ""),
        
        # Expected to IGNORE ❌
        ("Nico open calendar", False, ""),
        ("Zika is a virus", False, ""),
        ("Z.", False, ""),
        ("Z", False, ""),
        ("sorry, ziko open mail", False, ""),  # ليس في البداية
        ("play some music", False, ""),
    ]
    
    print("📋 Functional Tests:")
    print("-" * 70)
    
    passed = 0
    total_time = 0
    
    for text, expected_wake, expected_cmd in test_cases:
        start = time.perf_counter()
        has_wake, remainder, wake_form = extract_after_wake(text)
        elapsed = time.perf_counter() - start
        total_time += elapsed
        
        # Validation
        success = (has_wake == expected_wake)
        if success and expected_wake:
            success = (remainder == expected_cmd)
        
        status = "✅" if success else "❌"
        passed += 1 if success else 0
        
        print(f"{status} '{text[:40]}'")
        if has_wake:
            print(f"   Wake: '{wake_form}' → Command: '{remainder}'")
        print(f"   Time: {elapsed*1000:.4f}ms")
        print()
    
    print("=" * 70)
    print(f"Results: {passed}/{len(test_cases)} passed ({'✅' if passed == len(test_cases) else '❌'})")
    print(f"Average time: {(total_time/len(test_cases))*1000:.4f}ms")
    print()
    
    # ===== Performance Stress Test =====
    print("⚡ Performance Stress Test:")
    print("-" * 70)
    
    test_texts = [
        "زيكو افتح البريد الإلكتروني",
        "Ziko play some music",
        "hey zico what's the weather",
        "not a wake word at all"
    ]
    
    for test_text in test_texts:
        iterations = 5000
        start = time.perf_counter()
        
        for _ in range(iterations):
            extract_after_wake(test_text)
        
        elapsed = time.perf_counter() - start
        avg_us = (elapsed / iterations) * 1_000_000  # microseconds
        
        print(f"Text: '{test_text[:35]}'")
        print(f"  {iterations} iterations: {elapsed*1000:.2f}ms")
        print(f"  Average: {avg_us:.2f}μs per call")
        print(f"  Throughput: {iterations/elapsed:.0f} calls/sec")
        print()
    
    print("=" * 70)
    print("✨ Optimization: NO Levenshtein, O(1) lookups only!")
    print("🎯 Perfect for Raspberry Pi Zero with minimal CPU usage")
    print("=" * 70)