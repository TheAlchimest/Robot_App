# ------------------- Import Libraries -------------------
from Config import Config
import requests
import json

config = Config()

session_id = config.DEVICE_ID

def chat(message):
    """Optimized chat function"""
    if not message:
        return ""
    
    url = "http://localhost:5678/webhook/chat"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "sessionId": session_id,
        "message": message
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        
        # حل: استخدم response.json() بدل content
        data = response.json()
        print(data)              # يطبع الديكشنري كامل
        print(data["output"])    # يطبع النص اللي راجع
        
        return data["output"]
        
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return ""
    
    
if __name__ == "__main__":
    chat("Hello")
