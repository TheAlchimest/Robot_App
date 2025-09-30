# ------------------- Import Libraries -------------------
import json
import os
from threading import Lock

MEMORY_FILE = "chat-memory.json"

# Lock for protection in multi-threading
memory_lock = Lock()

# Cache for memory in RAM
_memory_cache = None
_cache_dirty = False

def load_memory():
    """Load memory with caching"""
    global _memory_cache
    
    if _memory_cache is not None:
        return _memory_cache
    
    with memory_lock:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                _memory_cache = json.load(file)
        else:
            _memory_cache = {"Important": [], "Not Important": []}
    
    return _memory_cache

def save_memory(memory):
    """Save memory with optimization"""
    global _memory_cache, _cache_dirty
    
    with memory_lock:
        _memory_cache = memory
        _cache_dirty = True
        
        # Direct save (can be deferred for optimization)
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(memory, file, indent=2, ensure_ascii=False)
        
        _cache_dirty = False

def update_memory(u_input, nova_response, flag):
    """Update memory with optimization"""
    memory = load_memory()

    if not isinstance(memory, dict):
        memory = {"Important": [], "Not Important": []}

    entry = {"user_input": u_input, "ai_response": nova_response}

    if flag == "Important":
        memory["Important"].append(entry)
    else:
        memory["Not Important"].append(entry)

    save_memory(memory)

def get_limited_conversation_history(limit=5):
    """Get only last N messages"""
    memory = load_memory()

    if not isinstance(memory, dict):
        return ""

    # Get last N messages from each category
    important = memory.get("Important", [])[-limit:]
    not_important = memory.get("Not Important", [])[-limit:]
    
    # Merge and sort by time (newest at the end by default)
    all_messages = important + not_important
    
    history = "\n".join(
        f"User: {entry['user_input']}\nAI: {entry['ai_response']}"
        for entry in all_messages[-limit:]
    )
    
    return history

def get_conversation_history():
    """Get all conversations (for backward compatibility)"""
    memory = load_memory()

    if not isinstance(memory, dict):
        return ""

    history = "\n".join(
        f"User: {entry['user_input']}\nAI: {entry['ai_response']}"
        for key in ["Important", "Not Important"]
        for entry in memory.get(key, [])
    )
    return history

def check_memory_percentage():
    """Check memory size"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        json_string = json.dumps(data)
        full_length = len(json_string)
        max_length = 10000
        percentage = (full_length / max_length) * 100

        return percentage, full_length

    return 0, 0

def delete_not_important_memory():
    """Delete non-important messages"""
    memory = load_memory()

    if "Not Important" in memory and memory["Not Important"]:
        memory["Not Important"] = []
        save_memory(memory)
        print("✅ Non-important messages deleted")
    else:
        print("⚠️ No non-important messages to delete")

def cleanup_old_messages(keep_important=20, keep_not_important=10):
    """Automatic cleanup of old messages"""
    memory = load_memory()
    
    if "Important" in memory:
        memory["Important"] = memory["Important"][-keep_important:]
    
    if "Not Important" in memory:
        memory["Not Important"] = memory["Not Important"][-keep_not_important:]
    
    save_memory(memory)
    print(f"✅ Memory cleaned up")