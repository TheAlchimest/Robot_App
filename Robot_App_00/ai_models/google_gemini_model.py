# ------------------- Import Libraries -------------------

import io
import json
import os
import tempfile

import google.generativeai as genai
from  ai_models import chat_history_manager   as history

# Load environment variables from .env file
from Config import Config
config = Config()

# Configure API keys
genai.configure(api_key=config.GEMINI_API_KEY)


# ------------------- AI Prompt -------------------
ROBOT_PROMPT = config.ROBOT_PROMPT




# AI Model Response Function
def ai_model_response(u_input, conversation):
    model = genai.GenerativeModel('gemini-2.5-flash')
    full_prompt = f"{ROBOT_PROMPT}\nConversation History:\n{conversation}\nUser: {u_input}"
    response = model.generate_content(full_prompt)
    return response.text.strip()


def chat(user_input):
    try:
        if user_input:
            conversation_history = history.get_conversation_history()
            ai_response = ai_model_response(user_input, conversation_history)

            # Ensure AI response is in the expected format
            if ai_response.startswith("[") and ai_response.endswith("]"):
                # Attempt to parse the response
                status, req_response = ai_response.strip('[]').split(", ", 1)
            else:
                status = "Not Important"
                req_response = ai_response  # Use the full response if not formatted correctly

            history.update_memory(user_input, req_response, status)
            print(f"AI Response: {req_response}")
            return req_response
        else:
            return ""
    finally:
        # Display memory usage percentage at the end of the program
        percentage, _ = history.check_memory_percentage()
        print(f"Memory usage till now: {percentage:.2f}%")

        # Delete "Not Important" memory if usage exceeds 10%
        if percentage > 10:
            print("Memory usage exceeds the limit. Deleting 'Not Important' memory...")
            history.delete_not_important_memory()
            # Recheck memory usage after deletion
            percentage, _ = history.check_memory_percentage()
            print(f"Updated memory usage: {percentage:.2f}%")


    


# Main Program Execution
if __name__ == "__main__":
   chat("Hello, How are You Today?")