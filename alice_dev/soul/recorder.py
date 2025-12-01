import os
import json
from datetime import datetime
from typing import Dict, Any, List
from config.settings import settings

class DataRecorder:
    def __init__(self, storage_dir: str = "/storage"):
        self.storage_dir = storage_dir
        self.perception_log_path = os.path.join(storage_dir, "perception_logs.jsonl")
        self.thought_log_path = os.path.join(storage_dir, "thought_logs.jsonl")
        
        # Ensure directory exists
        os.makedirs(storage_dir, exist_ok=True)

    def _append_log(self, file_path: str, data: Dict[str, Any]):
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                **data
            }
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error writing to log {file_path}: {e}")

    def log_perception(self, input_messages: List[Dict[str, str]], output_content: str, metadata: Dict[str, Any] = None):
        if not settings.ENABLE_LLM_LOGS:
            return
            
        data = {
            "input": input_messages,
            "output": output_content,
            "metadata": metadata or {}
        }
        self._append_log(self.perception_log_path, data)

    def log_thought(self, input_messages: List[Dict[str, str]], output_content: str, metadata: Dict[str, Any] = None):
        if not settings.ENABLE_LLM_LOGS:
            return

        data = {
            "input": input_messages,
            "output": output_content,
            "metadata": metadata or {}
        }
        self._append_log(self.thought_log_path, data)

# Global instance
recorder = DataRecorder()
