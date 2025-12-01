from typing import List, Dict, Deque, Any
from collections import deque
import json
import os

class WorkingMemory:
    """
    Manages the short-term context window (chat history) and perception queue.
    """
    def __init__(self, user_id: str = "default", max_history: int = 20, perception_size: int = 10):
        self.user_id = user_id
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        
        # Raw Perception Buffer: Accumulates raw sensory data before summarization
        self.perception_buffer: List[str] = []
        
        # Instant Memory Queue: FIFO queue for summarized perceptions (Short-term/Instant Memory)
        self.instant_memory_queue: Deque[str] = deque(maxlen=perception_size)
        
        self.senses_dir = "/storage/senses"
        os.makedirs(self.senses_dir, exist_ok=True)
        
        self._load_persistence()

    def write_to_sense(self, sense: str, content: str):
        """Writes content to a specific sense file."""
        try:
            file_path = os.path.join(self.senses_dir, f"{sense}.txt")
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception as e:
            print(f"Error writing to sense {sense}: {e}")

    def read_and_clear_senses(self) -> Dict[str, List[str]]:
        """Reads all sense files and clears them."""
        senses_data = {}
        sense_files = ["sight", "hearing", "smell", "taste", "touch", "mind"]
        
        for sense in sense_files:
            file_path = os.path.join(self.senses_dir, f"{sense}.txt")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                    
                    if lines:
                        senses_data[sense] = lines
                        
                    # Clear the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        pass
                except Exception as e:
                    print(f"Error reading/clearing sense {sense}: {e}")
        
        return senses_data

    def _get_persistence_path(self):
        return f"/storage/working_memory_{self.user_id}.json"

    def _load_persistence(self):
        """Loads state from persistence file."""
        try:
            path = self._get_persistence_path()
            
            # Migration: Check for old file if new one doesn't exist
            if not os.path.exists(path):
                # Check for previous locations
                old_path_v1 = f"/memory/working_memory_{self.user_id}.json"
                old_path_v0 = "/memory/working_memory.json"
                
                source_path = None
                if os.path.exists(old_path_v1):
                    source_path = old_path_v1
                elif os.path.exists(old_path_v0):
                    source_path = old_path_v0
                    
                if source_path:
                    print(f"Migrating working memory from {source_path} to {path}")
                    try:
                        with open(source_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # Load data
                        if "history" in data:
                            self.history = data["history"]
                        if "instant_memory_queue" in data:
                            self.instant_memory_queue = deque(data["instant_memory_queue"], maxlen=self.instant_memory_queue.maxlen)
                        
                        # Normalize roles immediately upon migration
                        for msg in self.history:
                            if msg.get("role") == "User":
                                msg["role"] = "user"
                            if msg.get("role") == "Alice":
                                msg["role"] = "assistant"

                        # Save to new path immediately
                        self._save_persistence()
                        return
                    except Exception as e:
                        print(f"Error migrating working memory: {e}")

            if os.path.exists(path):
                print(f"Loading working memory from {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if "history" in data:
                    self.history = data["history"]
                    # Normalize roles for frontend compatibility
                    for msg in self.history:
                        if msg.get("role") == "User":
                            msg["role"] = "user"
                        if msg.get("role") == "Alice":
                            msg["role"] = "assistant"
                            
                if "instant_memory_queue" in data:
                    self.instant_memory_queue = deque(data["instant_memory_queue"], maxlen=self.instant_memory_queue.maxlen)
        except Exception as e:
            print(f"Error loading working memory persistence: {e}")

    def _save_persistence(self):
        """Saves current state to persistence file."""
        try:
            path = self._get_persistence_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            data = {
                "history": self.history,
                "instant_memory_queue": list(self.instant_memory_queue)
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving working memory persistence: {e}")

    def add_message(self, role: str, content: str, **kwargs):
        """Adds a message to the conversation history."""
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.history.append(msg)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self._save_persistence()

    def add_event(self, type: str, content: str, data: Dict[str, Any] = None):
        """Adds a system event (thought, action, etc.) to history."""
        msg = {
            "role": type, # Use type as role for internal storage if convenient, or separate
            "type": type,
            "content": content,
            "actionData": data
        }
        self.history.append(msg)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self._save_persistence()

    def add_to_buffer(self, content: str):
        """Adds raw data to the perception buffer."""
        self.perception_buffer.append(content)
        
    def get_buffer_contents(self) -> List[str]:
        """Returns current buffer contents."""
        return list(self.perception_buffer)
        
    def clear_buffer(self):
        """Clears the perception buffer."""
        self.perception_buffer.clear()

    def add_instant_memory(self, content: str):
        """Adds a summarized memory to the instant memory queue."""
        self.instant_memory_queue.append(content)
        self._save_persistence()

    def get_context_string(self) -> str:
        """
        Returns the history formatted as a string for the LLM prompt.
        Filters out non-chat events (thoughts, actions) to keep context clean,
        unless we decide they are relevant.
        """
        context_msgs = []
        for msg in self.history:
            role = msg.get("role")
            # Only include standard chat roles for the LLM context
            if role in ["user", "assistant", "system"]:
                # If name is present, use it? Or just role?
                # The prompt expects "User: ..." or "Alice: ..."
                # If we stored role="user", content="...", name="Bob"
                # We might want to format as "Bob: ..."
                name = msg.get("name", role)
                context_msgs.append(f"{name}: {msg['content']}")
            # We skip 'thought', 'action', 'thinking_process' for the LLM context string
            # as they are usually internal or already summarized in perception.
            
        return "\n".join(context_msgs)

    def get_instant_memory_string(self) -> str:
        """
        Returns the instant memory queue formatted string.
        """
        if not self.instant_memory_queue:
            return "（瞬时记忆为空）"
        
        lines = []
        # 队列顺序：由远至近 (Oldest to Newest)
        # index 0 是最早的记忆，最后一个 index 是最新的记忆
        for i, item in enumerate(self.instant_memory_queue):
            # Mark the latest item
            prefix = f"[{i+1}]"
            lines.append(f"{prefix} {item}")
        return "\n".join(lines)

    def clear(self):
        self.history = []
        self.perception_buffer.clear()
        self.instant_memory_queue.clear()
        self._save_persistence()
