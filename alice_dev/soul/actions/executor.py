from typing import Dict, List, Any
from .registry import ActionRegistry

class ActionExecutor:
    def __init__(self, registry: ActionRegistry):
        self.registry = registry

    async def execute_queue(self, action_queue: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for item in action_queue:
            name = item.get("name")
            params = item.get("parameters", {})
            action = self.registry.get_action(name)
            
            if action:
                try:
                    result = await action.execute(context, **params)
                    results.append(result)
                except Exception as e:
                    results.append({"error": f"Failed to execute {name}: {str(e)}"})
            else:
                results.append({"error": f"Action {name} not found"})
        return results
