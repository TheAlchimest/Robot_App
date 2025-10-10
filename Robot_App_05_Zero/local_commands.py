"""
Local Command Handler - Process commands without API calls
Handles greetings, farewells, simple queries, and system control
"""

import re
from datetime import datetime
import random
from typing import Tuple, Optional

# ------------------- Command Patterns -------------------

GREETING_PATTERNS = {
    'english': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy'],
    'arabic':  ['مرحبا', 'هلا', 'اهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير', 'اهلين']
}

GOODBYE_PATTERNS = {
    'english': ['bye', 'goodbye', 'see you', 'talk to you later', 'good night', 'catch you later'],
    'arabic':  ['مع السلامة', 'الى اللقاء', 'وداعا', 'باي', 'تصبح على خير', 'بكرة نتكلم']
}

THANK_YOU_PATTERNS = {
    'english': ['thank you', 'thanks', 'thank you very much', 'appreciate it', 'thx'],
    'arabic':  ['شكرا', 'شكرا لك', 'شكرا جزيلا', 'مشكور', 'يعطيك العافية']
}

TIME_PATTERNS = {
    'english': ["what time is it", "what's the time", 'tell me the time', 'current time', 'time now'],
    'arabic':  ['كم الساعة', 'ما الوقت', 'الوقت الان', 'اي ساعة الان']
}

DATE_PATTERNS = {
    'english': ["what date is it", "what's the date", "today's date", 'what day is it'],
    'arabic':  ['ما التاريخ', 'التاريخ اليوم', 'اي يوم اليوم', 'كم التاريخ']
}

PAUSE_PATTERNS = {
    'english': ['pause', 'stop listening', 'sleep mode', 'go to sleep', 'standby', 'rest'],
    'arabic':  ['توقف', 'نام', 'ايقاف مؤقت', 'استراحة', 'ارتاح']
}

RESUME_PATTERNS = {
    'english': ['wake up', 'resume', 'start listening', 'are you there', 'come back'],
    'arabic':  ['استيقظ', 'استمر', 'ارجع', 'موجود', 'يلا']
}

HOW_ARE_YOU_PATTERNS = {
    'english': ['how are you', "how's it going", 'how do you do', "what's up", 'you okay'],
    'arabic':  ['كيف حالك', 'كيفك', 'شلونك', 'ايش اخبارك', 'عامل ايه']
}

HELP_PATTERNS = {
    'english': ['help', 'what can you do', 'your capabilities', 'commands', 'how to use'],
    'arabic':  ['مساعدة', 'ماذا تستطيع', 'الاوامر', 'كيف استخدمك', 'وش تقدر تسوي']
}

# ------------------- Response Templates -------------------

GREETING_RESPONSES = {
    'english': [
        "Hello! How can I help you?",
        "Hi there! What can I do for you?",
        "Hey! I'm here to assist you.",
        "Good to hear from you! How may I help?"
    ],
    'arabic': [
        "مرحبا! كيف يمكنني مساعدتك؟",
        "أهلا! في خدمتك.",
        "هلا! شو احتياجك؟",
        "اهلين! كيف اقدر اخدمك؟"
    ]
}

GOODBYE_RESPONSES = {
    'english': [
        "Goodbye! Say 'hello' when you need me again.",
        "See you later! Just call me when you're ready.",
        "Take care! I'll be here when you need me.",
        "Bye! Wake me up anytime with 'hello'."
    ],
    'arabic': [
        "مع السلامة! قل مرحبا عندما تحتاجني.",
        "الى اللقاء! ناديني متى احتجتني.",
        "الله يسلمك! انا هنا متى احتجتني.",
        "باي! صحيني بكلمة مرحبا."
    ]
}

THANK_YOU_RESPONSES = {
    'english': [
        "You're welcome! Happy to help.",
        "My pleasure! Anytime you need assistance.",
        "Glad I could help!",
        "No problem at all!"
    ],
    'arabic': [
        "عفوا! سعيد بمساعدتك.",
        "على الرحب والسعة!",
        "تشرفنا! اي خدمة.",
        "لا شكر على واجب!"
    ]
}

HOW_ARE_YOU_RESPONSES = {
    'english': [
        "I'm doing great, thank you! Ready to assist you.",
        "All systems running smoothly! How about you?",
        "I'm excellent! What can I help you with?",
        "Working perfectly! What do you need?"
    ],
    'arabic': [
        "بخير الحمد لله! جاهز لمساعدتك.",
        "تمام! كيف حالك انت؟",
        "كويس جدا! شو احتياجك؟",
        "شغال تمام! وش احتياجك؟"
    ]
}

PAUSE_RESPONSES = {
    'english': [
        "Going to sleep mode. Say 'hello' or 'wake up' to resume.",
        "Entering standby. Wake me up when you need me.",
        "Taking a break. Call me with 'hello' anytime."
    ],
    'arabic': [
        "داخل وضع النوم. قل مرحبا للعودة.",
        "ماشي، مستني نداك.",
        "راح ارتاح. ناديني متى احتجتني."
    ]
}

RESUME_RESPONSES = {
    'english': [
        "Hello! I'm back and ready to help you.",
        "I'm here! What do you need?",
        "Ready for action! How can I assist?",
        "Awake and ready! What's up?"
    ],
    'arabic': [
        "مرحبا! رجعت وجاهز لمساعدتك.",
        "موجود! شو احتياجك؟",
        "جاهز! كيف اقدر اساعدك؟",
        "صاحي! وش تبغى؟"
    ]
}

HELP_RESPONSES = {
    'english': """I can help you with many things! Here are some commands:
• Say 'bye' or 'goodbye' to pause me
• Say 'hello' or 'hi' to wake me up
• Ask 'what time is it' for current time
• Ask 'what date is it' for current date
• Say 'thank you' when I help you
• Ask me anything else and I'll use AI to help!""",
    'arabic': """يمكنني مساعدتك بأشياء كثيرة! إليك بعض الأوامر:
• قل 'مع السلامة' لإيقافي مؤقتاً
• قل 'مرحبا' لإيقاظي
• اسأل 'كم الساعة' لمعرفة الوقت
• اسأل 'ما التاريخ' لمعرفة التاريخ
• قل 'شكرا' عندما أساعدك
• اسألني أي شيء آخر وسأستخدم الذكاء الاصطناعي!"""
}

# ------------------- Utility Functions -------------------

def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    text = text.lower().strip()
    # Keep letters/digits/space and Arabic range
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_language(text: str) -> str:
    """Detect if text is primarily English or Arabic."""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars  = len(re.findall(r'[\w\u0600-\u06FF]', text))
    if total_chars == 0:
        return 'english'
    return 'arabic' if (arabic_chars / total_chars) > 0.3 else 'english'

def word_boundary_patterns(words) -> re.Pattern:
    """
    Compile a regex with word boundaries for a list of phrases.
    Matches full words/phrases to avoid 'hi' inside 'this'.
    """
    # Escape each phrase and allow one or more spaces between words
    # Example: 'good morning' -> r'\bgood\s+morning\b'
    parts = []
    for w in words:
        w_norm = normalize_text(w)
        parts.append(r'\b' + r'\s+'.join(map(re.escape, w_norm.split())) + r'\b')
    return re.compile('|'.join(parts), flags=re.IGNORECASE)

def has_any(text: str, patterns) -> bool:
    """Return True if any pattern matches text (with boundaries)."""
    rx = word_boundary_patterns(patterns)
    return rx.search(normalize_text(text)) is not None

def pick_response(responses, text: str) -> str:
    """Pick response according to detected language."""
    lang = detect_language(text)
    if isinstance(responses, dict):
        return random.choice(responses.get(lang, responses['english']))
    return responses

def get_local_time() -> str:
    now = datetime.now()
    return now.strftime("%I:%M %p")

def get_local_date() -> str:
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y")

# ------------- Greeting + Question Handling Helpers -------------

# Words that indicate the user is asking/continuing (beyond a pure greeting)
QUESTION_HINTS_EN = [
    'what', 'how', 'why', 'when', 'where', 'who', 'which',
    'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does',
    'please', 'help', 'explain', 'tell', 'show'
]
QUESTION_HINTS_AR = [
    'ما', 'ماذا', 'كيف', 'لماذا', 'متى', 'أين', 'مين', 'من', 'ايش', 'هل',
    'وش', 'يا ريت', 'ممكن', 'رجاء', 'ساعد', 'اشرح', 'وضح', 'قل', 'اعرض'
]

def split_greeting_and_remainder(text: str) -> Tuple[Optional[str], str]:
    """
    If text starts with a greeting phrase, return (greeting_phrase, remainder_text_without_greeting_prefix).
    Otherwise return (None, original_text).
    """
    norm = normalize_text(text)

    # Build combined greeting list preserving phrase order by length (longest first)
    combined = GREETING_PATTERNS['english'] + GREETING_PATTERNS['arabic']
    # Sort by length desc to catch longer phrases first
    combined_sorted = sorted(combined, key=lambda s: len(normalize_text(s)), reverse=True)

    for phrase in combined_sorted:
        p_norm = normalize_text(phrase)
        # ^\bPHRASE\b(?:\s+|$)
        rx = re.compile(r'^' + r'\b' + r'\s+'.join(map(re.escape, p_norm.split())) + r'\b(?:\s+|$)', re.IGNORECASE)
        m = rx.match(norm)
        if m:
            remainder = norm[m.end():].strip()
            return phrase, remainder
    return None, norm

def looks_like_question_or_command(text: str) -> bool:
    """
    Heuristics to decide if remainder has actionable content:
    - Contains question mark
    - Starts with or contains question/command hints
    - Has >= 2 words (beyond 1-word chit-chat)
    """
    if not text:
        return False
    if '?' in text:
        return True
    tokens = text.split()
    if len(tokens) >= 2:
        return True
    # hints by language
    has_en_hint = any(re.search(r'\b' + re.escape(h) + r'\b', text) for h in QUESTION_HINTS_EN)
    has_ar_hint = any(h in text for h in QUESTION_HINTS_AR)  # Arabic tokenization is looser
    return has_en_hint or has_ar_hint

# ------------------- Main Command Handler -------------------

def handle_local_command(text: str):
    """
    Handle commands locally without calling API.

    Returns:
        tuple: (should_continue, response, action, passthrough_text)
        - should_continue: True to continue to API, False if handled locally
        - response: Optional local response to speak/display
        - action: 'pause', 'resume', or None
        - passthrough_text: text to send to API (may have greeting stripped)
    """


    
    if not text or not text.strip():
        return True, None, None, ""

    original_text = text
    norm_text = normalize_text(original_text)

    # 1) Pause / Resume / Goodbye (control has priority)
    if has_any(norm_text, PAUSE_PATTERNS['english'] + PAUSE_PATTERNS['arabic']):
        return False, pick_response(PAUSE_RESPONSES, original_text), 'pause', ""

    if has_any(norm_text, RESUME_PATTERNS['english'] + RESUME_PATTERNS['arabic']):
        return False, pick_response(RESUME_RESPONSES, original_text), 'resume', ""

    if has_any(norm_text, GOODBYE_PATTERNS['english'] + GOODBYE_PATTERNS['arabic']):
        return False, pick_response(GOODBYE_RESPONSES, original_text), 'pause', ""

    # 2) Greetings: allow "greeting + question" to passthrough
    greeting_phrase, remainder = split_greeting_and_remainder(original_text)

    if greeting_phrase is not None:
        # Pure greeting (no remainder or remainder not actionable) => local response only
        if not remainder or not looks_like_question_or_command(remainder):
            return False, pick_response(GREETING_RESPONSES, original_text), 'resume', ""
        # Greeting + meaningful content => short greeting + continue to API with the remainder
        short_greet = pick_response(GREETING_RESPONSES, original_text)
        # Continue to API; pass only the remainder (clean of the greeting)
        return True, short_greet, 'resume', remainder

    # 3) Thank you / How are you / Help / Time / Date
    if has_any(norm_text, THANK_YOU_PATTERNS['english'] + THANK_YOU_PATTERNS['arabic']):
        return False, pick_response(THANK_YOU_RESPONSES, original_text), None, ""

    if has_any(norm_text, HOW_ARE_YOU_PATTERNS['english'] + HOW_ARE_YOU_PATTERNS['arabic']):
        return False, pick_response(HOW_ARE_YOU_RESPONSES, original_text), None, ""

    if has_any(norm_text, HELP_PATTERNS['english'] + HELP_PATTERNS['arabic']):
        lang = detect_language(original_text)
        return False, HELP_RESPONSES[lang], None, ""

    if has_any(norm_text, TIME_PATTERNS['english'] + TIME_PATTERNS['arabic']):
        current_time = get_local_time()
        lang = detect_language(original_text)
        resp = f"الوقت الآن {current_time}" if lang == 'arabic' else f"The current time is {current_time}"
        return False, resp, None, ""

    if has_any(norm_text, DATE_PATTERNS['english'] + DATE_PATTERNS['arabic']):
        current_date = get_local_date()
        lang = detect_language(original_text)
        resp = f"التاريخ اليوم {current_date}" if lang == 'arabic' else f"Today is {current_date}"
        return False, resp, None, ""

    # 4) Default → continue to API with original text
    return True, None, None, original_text

# ------------------- Testing -------------------

if __name__ == "__main__":
    tests = [
        # Pure greetings (local only)
        "hello",
        "مرحبا",
        "good morning",
        "السلام عليكم",

        # Greeting + question (should greet and CONTINUE to API with remainder)
        "hello, how can I integrate n8n with telegram?",
        "مرحبا، ازاي اربط n8n بالتليجرام؟",
        "hi please explain yarp routing setup",
        "اهلا ممكن توضحلي مشكلة scaffold db context؟",

        # Local controls
        "bye",
        "مع السلامة",
        "wake up",
        "استيقظ",

        # Local simple Qs
        "what time is it",
        "كم الساعة",
        "what date is it",
        "ما التاريخ",

        # Others → go to API
        "explain repository pattern in dotnet",
        "اشرح الفرق بين dapper و ef core"
    ]

    print("Testing Local Command Handler:\n")
    for t in tests:
        cont, resp, act, pass_text = handle_local_command(t)
        print(f"Input: {t}")
        print(f"Response: {resp}")
        print(f"Action: {act}")
        print(f"Continue to API: {cont}")
        print(f"Passthrough: {pass_text}")
        print("-" * 50)
