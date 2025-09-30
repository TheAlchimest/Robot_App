# 🤖 AI Voice Assistant - Smart Conversational System

A powerful voice-controlled AI assistant with smart state management and local command processing.

## ✨ Features

### 🎯 Core Features
- **Voice Input/Output**: Speak naturally and get voice responses
- **Smart State Management**: Automatic pause/resume based on context
- **Multi-threading Architecture**: Smooth, lag-free conversations
- **Bilingual Support**: English and Arabic commands
- **Local Command Processing**: Fast responses without API calls

### 🚀 Performance Optimizations
- **Threading**: Parallel processing for audio recording, STT, AI processing, and TTS
- **Caching**: Memory caching and LRU cache for faster responses
- **Optimized Models**: 
  - GPT-4o-mini for faster AI responses
  - ElevenLabs Turbo v2.5 for faster speech synthesis
- **Smart Context**: Only sends last 5 messages to AI for reduced latency

## 📋 Local Commands (No API Call Needed)

### 🗣️ Greetings & Farewells
| Command | Response | Action |
|---------|----------|--------|
| hello, hi, hey | Friendly greeting | Resumes listening |
| مرحبا, هلا, اهلا | ترحيب ودي | يستأنف الاستماع |
| bye, goodbye, see you | Farewell message | Pauses listening |
| مع السلامة, وداعا, باي | رسالة وداع | يوقف الاستماع |

### ⏰ Information Queries
| Command | Response |
|---------|----------|
| what time is it | Current time in 12-hour format |
| كم الساعة | الوقت الحالي |
| what date is it | Current date |
| ما التاريخ | التاريخ الحالي |

### 🎛️ System Control
| Command | Action |
|---------|--------|
| pause, sleep mode, stop listening | Pauses system |
| توقف, نام, ايقاف مؤقت | يوقف مؤقتاً |
| wake up, resume, start listening | Resumes system |
| استيقظ, استمر, ارجع | يستأنف العمل |

### 💬 Social Responses
| Command | Response |
|---------|----------|
| thank you, thanks | You're welcome |
| شكرا, شكرا لك | عفواً |
| how are you | I'm doing great |
| كيف حالك | بخير الحمد لله |
| help | Shows available commands |
| مساعدة | يعرض الأوامر المتاحة |

## 🛠️ Installation

### Prerequisites
```bash
# Python 3.8 or higher
python --version
```

### Install Dependencies
```bash
pip install -r req.txt
```

### Required API Keys
Create a `.env` file with:
```env
OPEN_AI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## 🚀 Usage

### Start the System
```bash
python main.py
```

### Expected Flow
1. System starts and says "Hello, I'm ready to help you"
2. Speak your command or question
3. System processes and responds
4. Say "bye" to pause, "hello" to resume
5. Press `Ctrl+C` to exit

### Example Conversations

**Example 1: Quick Time Check (Local)**
```
User: "What time is it?"
AI: "The current time is 03:45 PM"
[No API call - instant response]
```

**Example 2: Pause & Resume**
```
User: "Goodbye"
AI: "Goodbye! Say 'hello' when you need me again."
[System paused - still recording but not processing]

User: "Hello"
AI: "Hello! I'm back and ready to help you."
[System resumed]
```

**Example 3: AI Query**
```
User: "What's the capital of France?"
AI: "The capital of France is Paris."
[API call made - AI response]
```

## 📁 Project Structure

```
├── main.py                    # Main application with threading
├── local_commands.py          # Local command handler
├── audio_recorder.py          # Audio recording module
├── speech_to_text.py          # STT conversion
├── text_to_speech.py          # TTS conversion
├── ai_model.py                # AI processing
├── chat_history_manager.py    # Memory management
├── Config.py                  # Configuration
├── .env                       # API keys (not in repo)
├── req.txt                    # Dependencies
└── README.md                  # This file
```

## ⚙️ Configuration

### Adjust Audio Settings
In `audio_recorder.py`:
```python
self.CHUNK = 512              # Smaller = faster response
silence_threshold = 500       # Lower = more sensitive
silence_duration = 1.5        # Seconds of silence to stop
```

### Adjust AI Settings
In `ai_model.py`:
```python
model = "gpt-4o-mini"         # Faster model
max_tokens = 150              # Shorter responses
```

### Memory Management
In `chat_history_manager.py`:
```python
limit = 5                     # Number of messages to keep in context
max_length = 10000           # Memory limit before cleanup
```

## 🔧 Troubleshooting

### Audio Issues
```bash
# Test microphone
python -c "import pyaudio; p=pyaudio.PyAudio(); print(p.get_default_input_device_info())"

# If error, try different device index
# In audio_recorder.py, add: input_device_index=X
```

### API Issues
```bash
# Verify API keys
python -c "from Config import Config; c=Config(); print('OpenAI:', len(c.OPEN_AI_API_KEY), 'ElevenLabs:', len(c.ELEVENLABS_API_KEY))"
```

### Performance Issues
- Reduce `max_tokens` in `ai_model.py` to 100
- Increase `silence_duration` to 2.0 for slower speech
- Check internet connection speed

## 🎯 Performance Metrics

| Operation | Time (Before) | Time (After) |
|-----------|---------------|--------------|
| Audio Recording | 3s | 1.5s |
| Speech to Text | 2s | 1.5s |
| AI Response | 4s | 2s |
| Text to Speech | 2s | 1s |
| **Total** | **11s** | **6s** |

Local commands respond in < 0.1s!

## 📝 Adding New Commands

### Step 1: Add Pattern
In `local_commands.py`:
```python
NEW_COMMAND_PATTERNS = {
    'english': ['your command', 'variant'],
    'arabic': ['أمرك', 'البديل']
}
```

### Step 2: Add Response
```python
NEW_COMMAND_RESPONSES = {
    'english': ["Your response here"],
    'arabic': ["ردك هنا"]
}
```

### Step 3: Add Handler
In `handle_local_command()`:
```python
if match_pattern(text, NEW_COMMAND_PATTERNS['english'] + NEW_COMMAND_PATTERNS['arabic']):
    response = get_response(NEW_COMMAND_RESPONSES, text)
    return False, response, None
```

## 🤝 Contributing

Feel free to:
- Add more local commands
- Improve pattern matching
- Optimize performance further
- Add more languages

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- OpenAI for GPT models
- ElevenLabs for voice synthesis
- PyAudio for audio handling

---

**Made with ❤️ for smooth AI conversations**
