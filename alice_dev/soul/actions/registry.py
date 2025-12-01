from typing import Dict, List, Any
from .base import Action
from .innate import (
    Daze, Recall, Associate, Memorize, LearnSkill, Speak, 
    ThinkAdd, ThinkUpdate, ThinkComplete, UpdateRelationship, AddBelief
)
from .express import Express
from .coding import ManageSkill, RunPython, RunBash
from .web import BrowseWeb, VisitPage
from .minecraft import (
    MinecraftConnect, MinecraftDisconnect, MinecraftStatus, MinecraftPerception,
    MinecraftChat, MinecraftMove, MinecraftMine, MinecraftPlace,
    MinecraftEquip, MinecraftCraft, MinecraftAttack
)
from . import learned
import importlib
from memory.store import WeaviateStore

class ActionRegistry:
    def __init__(self, memory_store: WeaviateStore):
        self.actions: Dict[str, Action] = {}
        self.innate_names = set()
        self.memory_store = memory_store
        self._init_innate()
        self._init_learned()

    def _init_innate(self):
        innate = [
            Daze(),
            Speak(),
            ThinkAdd(),
            ThinkUpdate(),
            ThinkComplete(self.memory_store),
            Recall(self.memory_store),
            Associate(self.memory_store),
            Memorize(self.memory_store),
            LearnSkill(self),
            UpdateRelationship(self.memory_store),
            AddBelief(self.memory_store),
            Express(),
            ManageSkill(self),
            RunPython(),
            RunBash(),
            BrowseWeb(),
            VisitPage(),
            # MinecraftConnect(),
            # MinecraftDisconnect(),
            MinecraftStatus(),
            MinecraftPerception(),
            MinecraftChat(),
            MinecraftMove(),
            MinecraftMine(),
            MinecraftPlace(),
            MinecraftEquip(),
            MinecraftCraft(),
            MinecraftAttack()
        ]
        for action in innate:
            self.innate_names.add(action.name)
            self.register(action)

    def _init_learned(self):
        # Clear existing learned actions first if reloading
        # But we store them in self.actions mixed with innate.
        # So we should track which are learned.
        # For simplicity, we just re-register, overwriting old ones.
        for action in learned.DEFAULT_LEARNED_ACTIONS:
            self.register(action)

    def reload_learned(self):
        """Reloads the learned actions module and updates the registry."""
        importlib.reload(learned)
        self._init_learned()
        print("Learned actions reloaded.")

    def register(self, action: Action):
        self.actions[action.name] = action

    def get_action(self, name: str) -> Action:
        # Try exact match first
        if name in self.actions:
            return self.actions[name]
        # Try case-insensitive match
        name_lower = name.lower()
        for key in self.actions:
            if key.lower() == name_lower:
                return self.actions[key]
        return None

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for name, action in self.actions.items():
            schema = action.to_schema()
            if name in self.innate_names:
                schema['origin'] = 'innate'
            else:
                schema['origin'] = 'learned'
            schemas.append(schema)
        return schemas
