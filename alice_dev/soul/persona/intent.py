from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Intent:
    life_goal: str = "探索世界和自己的内心，实现自我价值"
    long_term_goal: str = "了解学习周围的环境，建立深厚的人际关系"
    short_term_goal: str = "提问以获取信息"
    # thinking_pool: List[Dict[str, Any]] = field(default_factory=list) 
    # Structure: { "id": str, "topic": str, "content": str, "status": "active" }
    thinking_pool: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "life_goal": self.life_goal,
            "long_term_goal": self.long_term_goal,
            "short_term_goal": self.short_term_goal,
            "thinking_pool": self.thinking_pool
        }
