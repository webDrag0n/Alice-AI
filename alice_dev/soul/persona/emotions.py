from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Emotions:
    joy: float = 0.5
    anger: float = 0.0
    sorrow: float = 0.0
    fear: float = 0.0
    love: float = 0.0
    hate: float = 0.0
    desire: float = 0.5

    def to_dict(self) -> Dict[str, float]:
        return self.__dict__

    def update(self, updates: Dict[str, float]):
        for key, value in updates.items():
            if hasattr(self, key):
                # Clamp between 0.0 and 1.0
                new_val = max(0.0, min(1.0, value))
                setattr(self, key, new_val)
