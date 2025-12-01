from .emotions import Emotions
from .desires import Desires
from .intent import Intent
from typing import Dict, Any
import json
import os

class PersonaManager:
    def __init__(self, config_path: str = "config/persona.json"):
        self.config = self._load_config(config_path)
        
        self.emotions = Emotions(**self.config.get("emotions", {}))
        self.desires = Desires(**self.config.get("desires", {}))
        
        intent_data = self.config.get("intent", {})
        self.intent = Intent(
            life_goal=intent_data.get("life_goal", "探索世界和自己的内心，实现自我价值"),
            long_term_goal=intent_data.get("long_term_goal", "了解学习周围的环境，建立深厚的人际关系"),
            short_term_goal=intent_data.get("short_term_goal", "提问以获取信息")
        )
        
        # Load persistence if available
        self._load_persistence()

    def _get_persistence_path(self):
        return "/storage/persona_state.json"

    def _load_persistence(self):
        """Loads state from persistence file."""
        try:
            path = self._get_persistence_path()
            
            # Migration: Check for old file if new one doesn't exist
            if not os.path.exists(path):
                old_path = "/memory/persona_state.json"
                if os.path.exists(old_path):
                    print(f"Migrating persona state from {old_path} to {path}")
                    try:
                        with open(old_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Load data to memory
                        if "emotions" in data:
                            self.emotions.update(data["emotions"])
                        if "desires" in data:
                            self.desires.update(data["desires"])
                        if "intent" in data:
                            intent_data = data["intent"]
                            if "short_term_goal" in intent_data:
                                self.intent.short_term_goal = intent_data["short_term_goal"]
                            if "life_goal" in intent_data:
                                self.intent.life_goal = intent_data["life_goal"]
                            if "long_term_goal" in intent_data:
                                self.intent.long_term_goal = intent_data["long_term_goal"]
                            if "thinking_pool" in intent_data:
                                self.intent.thinking_pool = intent_data["thinking_pool"]
                        
                        # Save to new path immediately
                        self._save_persistence()
                        return
                    except Exception as e:
                        print(f"Error migrating persona state: {e}")

            if os.path.exists(path):
                print(f"Loading persona state from {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if "emotions" in data:
                    self.emotions.update(data["emotions"])
                if "desires" in data:
                    self.desires.update(data["desires"])
                if "intent" in data:
                    intent_data = data["intent"]
                    if "short_term_goal" in intent_data:
                        self.intent.short_term_goal = intent_data["short_term_goal"]
                    if "life_goal" in intent_data:
                        self.intent.life_goal = intent_data["life_goal"]
                    if "long_term_goal" in intent_data:
                        self.intent.long_term_goal = intent_data["long_term_goal"]
                    if "thinking_pool" in intent_data:
                        self.intent.thinking_pool = intent_data["thinking_pool"]
        except Exception as e:
            print(f"Error loading persona persistence: {e}")

    def _save_persistence(self):
        """Saves current state to persistence file."""
        try:
            path = self._get_persistence_path()
            # Ensure directory exists (it should, as it's a volume)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            state = self.get_state()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving persona persistence: {e}")

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            # Handle relative paths from project root
            if not os.path.isabs(path):
                # Assuming running from alice_dev root or similar
                # Better to find the project root dynamically or assume standard structure
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                full_path = os.path.join(base_path, path)
            else:
                full_path = path
                
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: Config file not found at {full_path}, using defaults.")
                return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_state(self) -> Dict[str, Any]:
        return {
            "emotions": self.emotions.to_dict(),
            "desires": self.desires.to_dict(),
            "intent": self.intent.to_dict()
        }

    def update_state(self, updates: Dict[str, Any]):
        if "emotions" in updates:
            self.emotions.update(updates["emotions"])
        if "desires" in updates:
            self.desires.update(updates["desires"])
        if "intent" in updates:
            intent_data = updates["intent"]
            if "short_term_goal" in intent_data:
                self.intent.short_term_goal = intent_data["short_term_goal"]
            if "life_goal" in intent_data:
                self.intent.life_goal = intent_data["life_goal"]
            if "long_term_goal" in intent_data:
                self.intent.long_term_goal = intent_data["long_term_goal"]
            
            # Allow direct update of thinking_pool (e.g. from API)
            if "thinking_pool" in intent_data:
                self.intent.thinking_pool = intent_data["thinking_pool"]

            # Handle Thinking Pool Actions
            if "thinking_pool_actions" in intent_data:
                actions = intent_data["thinking_pool_actions"]
                
                # Add
                for item in actions.get("add", []):
                    # Generate simple ID if not provided (though LLM should provide or we generate)
                    # Let's assume LLM provides topic and content, we generate ID
                    import uuid
                    new_id = str(uuid.uuid4())[:8]
                    self.intent.thinking_pool.append({
                        "id": new_id,
                        "topic": item.get("topic", "Unknown"),
                        "content": item.get("content", ""),
                        "status": "active"
                    })
                
                # Continue (Update content)
                for item in actions.get("continue", []):
                    target_id = item.get("id")
                    new_content = item.get("new_content")
                    for thought in self.intent.thinking_pool:
                        if thought["id"] == target_id:
                            thought["content"] += f" -> {new_content}"
                            break
                
                # Complete (Remove)
                for target_id in actions.get("complete", []):
                    self.intent.thinking_pool = [t for t in self.intent.thinking_pool if t["id"] != target_id]
        
        # Save state after update
        self._save_persistence()

    def get_persona_prompt(self, user_profile: Dict[str, Any] = None) -> str:
        """Generates the persona system prompt from configuration."""
        c = self.config
        basic = c.get("basic_info", {})
        traits = ", ".join(c.get("personality_traits", []))
        style = ", ".join(c.get("style_guide", []))
        
        user_section = ""
        if user_profile:
            user_section = f"\n**{user_profile.get('name', 'User')}**: {user_profile.get('profile', '')}"

        prompt = f"""
**身份**: {c.get('name', 'Agent')} ({basic.get('name', 'Agent')})
**设定**: {c.get('system_instructions', '')}
**外貌**: {basic.get('appearance', '')}
**起源**: {basic.get('origin', '')}
**住所**: {basic.get('residence', '')}
**性格**: {traits}
**风格**: {style}
{user_section}
"""
        return prompt.strip()
