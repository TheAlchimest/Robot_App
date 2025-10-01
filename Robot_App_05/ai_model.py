# ------------------- Import Libraries -------------------
from openai import OpenAI
import chat_history_manager as history
from Config import Config
from functools import lru_cache

config = Config()
client = OpenAI(api_key=config.OPEN_AI_API_KEY)

ROBOT_PROMPT = config.ROBOT_PROMPT

# Cache for similar responses
@lru_cache(maxsize=50)
def get_cached_response(user_input_hash):
    """Cache for repeated responses"""
    return None

def ai_model_response(u_input, conversation):
    """Optimized AI call"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Using faster model
        messages=[
            {"role": "system", "content": ROBOT_PROMPT},
            {"role": "user", "content": f"{conversation}\nUser: {u_input}"}
        ],
        max_tokens=1000,  # Reduced tokens for faster response
        temperature=0.7,
        stream=False  # Can enable stream for progressive response
    )
    
    return response.choices[0].message.content.strip()

def chat(user_input):
    """Optimized chat function"""
    if not user_input:
        return ""
    
    try:
        # Get only last 5 messages to reduce context
        conversation_history = history.get_limited_conversation_history(5)
        ai_response = ai_model_response(user_input, conversation_history)

        # Process response
        if ai_response.startswith("[") and ai_response.endswith("]"):
            try:
                status, req_response = ai_response.strip('[]').split(", ", 1)
            except ValueError:
                status = "Not Important"
                req_response = ai_response
        else:
            status = "Not Important"
            req_response = ai_response

        # Update memory asynchronously (in background)
        history.update_memory(user_input, req_response, status)
        
        # Automatic memory cleanup
        percentage, _ = history.check_memory_percentage()
        if percentage > 10:
            history.delete_not_important_memory()
        
        return req_response
        
    except Exception as e:
        print(f"AI error: {e}")
        return "Sorry, an error occurred during processing"

if __name__ == "__main__":
    chat("Hello")
