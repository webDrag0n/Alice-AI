from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ActionSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, str]  # name: description
    category: str = "general"

class Action(ABC):
    def __init__(self, name: str, description: str, parameters: Dict[str, str] = None, category: str = "general"):
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.category = category

    @abstractmethod
    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes the action.
        :param context: The current agent state/context.
        :param kwargs: Parameters for the action.
        :return: Result dictionary (e.g., {"output": "...", "state_update": {...}})
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category
        }
