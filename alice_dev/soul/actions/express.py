from typing import Any, Dict
from .base import Action

class Express(Action):
    def __init__(self):
        super().__init__(
            name="express",
            description="表达动作和表情。用于展示你的身体语言和面部表情，增强互动真实感。",
            parameters={
                "body": "身体动作 (idle, talking, listening, reading, sleeping, working, eating)",
                "face": "面部表情 (neutral, happy, sad, angry, surprised, shy, playful, concerned)"
            },
            category="expression"
        )

    async def execute(self, context: Dict[str, Any], body: str = "idle", face: str = "neutral", **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "express",
            "message": f"{agent_name} 做出动作: [身体:{body}, 表情:{face}]",
            "visual_state": {
                "body": body,
                "face": face
            }
        }
