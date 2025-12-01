# Development Guide

This guide covers the project structure and how to extend Alice AI's capabilities.

## Project Structure

```
alice_dev/
├── backend/            # FastAPI server & API routes
├── config/             # Configuration files (Persona, Settings)
├── docker/             # Docker Compose files
├── docs/               # Documentation
├── frontend/           # React application
├── memory/             # Memory management & Weaviate client
├── soul/               # Core Agent Logic (LangGraph)
│   ├── actions/        # Action definitions (Tools)
│   ├── llm/            # LLM Provider wrappers
│   ├── nodes/          # Graph nodes (Observe, Think, Act)
│   ├── persona/        # Emotion & Desire logic
│   └── prompts.py      # System prompts
└── storage/            # Local file storage (logs, backups)
```

## Extending the Agent

### 1. Adding New Actions (Tools)

Actions are the tools the agent uses to interact with the world. They are defined in `soul/actions/`.

**Step 1: Create the Action Class**
Inherit from `Action` and implement the `execute` method.

```python
# soul/actions/my_action.py
from typing import Dict, Any
from .base import Action

class MyNewAction(Action):
    def __init__(self):
        super().__init__(
            name="my_new_action",
            description="Description of what this action does.",
            parameters={
                "param1": "Description of param1"
            },
            category="custom"
        )

    async def execute(self, context: Dict[str, Any], param1: str, **kwargs) -> Dict[str, Any]:
        # Your logic here
        return {
            "event": "my_action_done",
            "message": f"Executed with {param1}",
            "data": { "result": "success" }
        }
```

**Step 2: Register the Action**
Add your action to `soul/actions/registry.py`.

```python
# soul/actions/registry.py
from .my_action import MyNewAction

class ActionRegistry:
    def _init_innate(self):
        innate = [
            # ... existing actions
            MyNewAction(),
        ]
```

### 2. Customizing the Persona

You can modify the agent's personality, backstory, and default goals in `config/persona.json`.

```json
{
  "basic_info": {
    "name": "Alice",
    "age": 20,
    "description": "A sentient AI assistant..."
  },
  "personality": {
    "traits": ["Curious", "Empathetic", "Logical"]
  }
}
```

### 3. Prompt Engineering

The core system prompts are located in `soul/prompts.py`.
- **`PERCEPTION_SYSTEM_PROMPT`**: Controls how the agent summarizes sensory input.
- **`THINK_NODE_SYSTEM_PROMPT`**: The master prompt for the reasoning engine.

## Key Concepts for Developers

- **Action Registry**: The central place where all available tools are defined. The `Think` node uses this to generate the list of available actions for the LLM.
- **Thinking Pool**: A mechanism for the agent to maintain long-running thought threads across multiple conversation turns.
- **Metacognition**: The agent has a self-reflection mechanism (defined in `soul/memory/metacognition.py`) that helps it understand its own state.
