# ------------------- Import Libraries -------------------
from Config import Config
import requests
import json

config = Config()

session_id = config.DEVICE_ID
n8n_url = config.N8N_URL
n8n_active_agent = "general"

def chat(message):
    """Optimized chat function"""
    if not message:
        return ""
    
    url = n8n_url
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "sessionId": session_id,
        "userId": session_id,
        "message": message,
        "activeAgent":n8n_active_agent
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        
        # حل: استخدم response.json() بدل content
        data = response.json()
        n8n_active_agent = data["activeAgent"];
        print(data["output"])    # يطبع النص اللي راجع
        
        return data["output"]
        
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return ""
    
    
if __name__ == "__main__":
    chat("Hello")
