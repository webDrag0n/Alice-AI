from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Desires:
    curiosity: float = 0.6
    social_connect: float = 0.4
    achievement: float = 0.5
    autonomy: float = 0.4
    bonding: float = 0.3
    competence: float = 0.5
    exploration: float = 0.5
    safety: float = 0.2
    order: float = 0.2
    novelty: float = 0.5
    influence: float = 0.3
    play: float = 0.4
    rest: float = 0.3
    stability: float = 0.2
    expression: float = 0.5

    def to_dict(self) -> Dict[str, float]:
        return self.__dict__

    def update(self, updates: Dict[str, float]):
        for key, value in updates.items():
            if hasattr(self, key):
                new_val = max(0.0, min(1.0, value))
                setattr(self, key, new_val)
