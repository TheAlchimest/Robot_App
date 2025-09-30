"""
Local Command Handler - Process commands without API calls
Handles greetings, farewells, simple queries, and system control
"""

import re
from datetime import datetime
import random

# ------------------- Command Patterns -------------------

GREETING_PATTERNS = {
    'english': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy'],
    'arabic': ['مرحبا', 'هلا', 'اهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير', 'اهلين']
}

GOODBYE_PATTERNS = {
    'english': ['bye', 'goodbye', 'see you', 'talk to you later', 'good night', 'catch you later'],
    'arabic': ['مع السلامة', 'الى اللقاء', 'وداعا', 'باي', 'تصبح على خير', 'بكرة نتكلم']
}

THANK_YOU_PATTERNS = {
    'english': ['thank you', 'thanks', 'thank you very much', 'appreciate it', 'thx'],
    'arabic': ['شكرا', 'شكرا لك', 'شكرا جزيلا', 'مشكور', 'يعطيك العافية']
}

TIME_PATTERNS = {
    'english': ['what time is it', 'what\'s the time', 'tell me the time', 'current time', 'time now'],
    'arabic': ['كم الساعة', 'ما الوقت', 'الوقت الان', 'اي ساعة الان']
}

DATE_PATTERNS = {
    'english': ['what date is it', 'what\'s the date', 'today\'s date', 'what day is it'],
    'arabic': ['ما التاريخ', 'التاريخ اليوم', 'اي يوم اليوم', 'كم التاريخ']
}

PAUSE_PATTERNS = {
    'english': ['pause', 'stop listening', 'sleep mode', 'go to sleep', 'standby', 'rest'],
    'arabic': ['توقف', 'نام', 'ايقاف مؤقت', 'استراحة', 'ارتاح']
}

RESUME_PATTERNS = {
    'english': ['wake up', 'resume', 'start listening', 'are you there', 'come back'],
    'arabic': ['استيقظ', 'استمر', 'ارجع', 'موجود', 'يلا']
}

HOW_ARE_YOU_PATTERNS = {
    'english': ['how are you', 'how\'s it going', 'how do you do', 'what\'s up', 'you okay'],
    'arabic': ['كيف حالك', 'كيفك', 'شلونك', 'ايش اخبارك', 'عامل ايه']
}

HELP_PATTERNS = {
    'english': ['help', 'what can you do', 'your capabilities', 'commands', 'how to use'],
    'arabic': ['مساعدة', 'ماذا تستطيع', 'الاوامر', 'كيف استخدمك', 'وش تقدر تسوي']
}

# ------------------- Response Templates -------------------

GREETING_RESPONSES = {
    'english': [
        "Hello! How can I help you today?",
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

def normalize_text(text):
    """Normalize text for pattern matching"""
    text = text.lower().strip()
    # Remove punctuation except Arabic characters
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    return text

def match_pattern(text, patterns):
    """Check if text matches any pattern in the list"""
    normalized = normalize_text(text)
    for pattern in patterns:
        if pattern in normalized or normalized in pattern:
            return True
    return False

def detect_language(text):
    """Detect if text is primarily English or Arabic"""
    # Count Arabic characters
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(re.findall(r'[\w\u0600-\u06FF]', text))
    
    if total_chars == 0:
        return 'english'
    
    # If more than 30% Arabic characters, consider it Arabic
    return 'arabic' if (arabic_chars / total_chars) > 0.3 else 'english'

def get_response(responses, text):
    """Get appropriate response based on text language"""
    lang = detect_language(text)
    if isinstance(responses, dict):
        return random.choice(responses.get(lang, responses['english']))
    return responses

def get_local_time():
    """Get current time in 12-hour format"""
    now = datetime.now()
    return now.strftime("%I:%M %p")

def get_local_date():
    """Get current date in readable format"""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y")

# ------------------- Main Command Handler -------------------

def handle_local_command(text):
    """
    Handle commands locally without calling API
    
    Args:
        text: User input text
    
    Returns:
        tuple: (should_continue, response, action)
        - should_continue: True if should continue to API, False if handled locally
        - response: The response to give (if handled locally)
        - action: 'pause', 'resume', or None
    """
    
    if not text or not text.strip():
        return True, None, None
    
    # Check for pause commands
    if match_pattern(text, PAUSE_PATTERNS['english'] + PAUSE_PATTERNS['arabic']):
        response = get_response(PAUSE_RESPONSES, text)
        return False, response, 'pause'
    
    # Check for resume commands
    if match_pattern(text, RESUME_PATTERNS['english'] + RESUME_PATTERNS['arabic']):
        response = get_response(RESUME_RESPONSES, text)
        return False, response, 'resume'
    
    # Check for goodbye (pause listening)
    if match_pattern(text, GOODBYE_PATTERNS['english'] + GOODBYE_PATTERNS['arabic']):
        response = get_response(GOODBYE_RESPONSES, text)
        return False, response, 'pause'
    
    # Check for greetings
    if match_pattern(text, GREETING_PATTERNS['english'] + GREETING_PATTERNS['arabic']):
        response = get_response(GREETING_RESPONSES, text)
        return False, response, 'resume'  # Ensure system is active on greeting
    
    # Check for thank you
    if match_pattern(text, THANK_YOU_PATTERNS['english'] + THANK_YOU_PATTERNS['arabic']):
        response = get_response(THANK_YOU_RESPONSES, text)
        return False, response, None
    
    # Check for how are you
    if match_pattern(text, HOW_ARE_YOU_PATTERNS['english'] + HOW_ARE_YOU_PATTERNS['arabic']):
        response = get_response(HOW_ARE_YOU_RESPONSES, text)
        return False, response, None
    
    # Check for help request
    if match_pattern(text, HELP_PATTERNS['english'] + HELP_PATTERNS['arabic']):
        lang = detect_language(text)
        response = HELP_RESPONSES[lang]
        return False, response, None
    
    # Check for time request
    if match_pattern(text, TIME_PATTERNS['english'] + TIME_PATTERNS['arabic']):
        current_time = get_local_time()
        lang = detect_language(text)
        if lang == 'arabic':
            response = f"الوقت الآن {current_time}"
        else:
            response = f"The current time is {current_time}"
        return False, response, None
    
    # Check for date request
    if match_pattern(text, DATE_PATTERNS['english'] + DATE_PATTERNS['arabic']):
        current_date = get_local_date()
        lang = detect_language(text)
        if lang == 'arabic':
            response = f"التاريخ اليوم {current_date}"
        else:
            response = f"Today is {current_date}"
        return False, response, None
    
    # No local command matched, proceed to API
    return True, None, None

# ------------------- Testing -------------------

if __name__ == "__main__":
    # Test cases
    test_inputs = [
        "hello",
        "مرحبا",
        "what time is it",
        "كم الساعة",
        "bye",
        "thank you",
        "شكرا",
        "how are you",
        "help"
    ]
    
    print("Testing Local Command Handler:\n")
    for test in test_inputs:
        should_continue, response, action = handle_local_command(test)
        print(f"Input: {test}")
        print(f"Response: {response}")
        print(f"Action: {action}")
        print(f"Continue to API: {should_continue}\n")
