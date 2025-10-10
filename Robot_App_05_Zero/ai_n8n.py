# ------------------- Import Libraries -------------------
from Config import Config
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = Config()

session_id = config.DEVICE_ID
n8n_url = config.N8N_URL
n8n_active_agent = "general"

def chat(message):
    """Optimized chat function"""
    print(F"chat:{message}")  # print safely
    global n8n_active_agent  # <-- Add this line
    print(F"n8n_active_agent:{n8n_active_agent}")  # print safely

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
        "activeAgent": n8n_active_agent
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        
        data = response.json()
        print("data returned")  # print safely
        print(F"data:{data}")  # print safely
        
        # Update active agent for next call
        n8n_active_agent = data.get("activeAgent", n8n_active_agent)
        output = data.get("output", "")
        print(F"n8n_active_agent:{n8n_active_agent}")  # print safely
        print(F"output:{output}")  # print safely
        
        print(data.get("output", ""))  # print safely
        return data.get("output", "")
        
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return ""
    

def test():
    return chat("can you hear me?")
    
if __name__ == "__main__":
    chat("Hello")
