# ------------------- Import Libraries -------------------

import io
import json
import os
import tempfile


# Load environment variables from .env file
#from Config import Config
#config = Config()

# Configure API keys
# File to store memory
#MEMORY_FILE = config.MEMORY_FILE
MEMORY_FILE = "chat-memory.json"
# Load Conversation Memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {"Important": [], "Not Important": []}  # Initialize memory structure if absent


# Save Conversation Memory
def save_memory(memory):
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)


# Label and Update Memory
def update_memory(u_input, nova_response, flag):
    memory = load_memory()

    # Ensure memory is initialized correctly
    if not isinstance(memory, dict):
        memory = {"Important": [], "Not Important": []}

    entry = {"user_input": u_input, "ai_response": nova_response}

    if flag == "Important":
        memory["Important"].append(entry)
    else:
        memory["Not Important"].append(entry)

    # Save the updated memory
    save_memory(memory)


# Generate Conversation History
def get_conversation_history():
    memory = load_memory()

    # Ensure memory is a dictionary with expected keys
    if not isinstance(memory, dict) or "Important" not in memory or "Not Important" not in memory:
        return ""

    history = "\n".join(
        f"[User: {entry['user_input']} AI: {entry['ai_response']}]"
        for key in ["Important", "Not Important"]
        for entry in memory[key]
    )
    return history


# Check Memory Percentage
def check_memory_percentage():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            data = json.load(file)

        json_string = json.dumps(data)
        full_length = len(json_string)

        max_length = 10000  # Set a limit for memory
        percentage = (full_length / max_length) * 100

        return percentage, full_length

    return 0, 0


# Delete Not Important Memory
def delete_not_important_memory():
    memory = load_memory()

    if "Not Important" in memory and memory["Not Important"]:
        memory["Not Important"] = []  # Clear the "Not Important" list
        save_memory(memory)
        print("All 'Not Important' entries have been deleted.")
    else:
        print("'Not Important' section is already empty.")

