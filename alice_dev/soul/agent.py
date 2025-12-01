import asyncio
import json
import os
from typing import Dict, Any, AsyncGenerator, Optional, Callable
from .persona.manager import PersonaManager
from .llm.provider import LLMProvider
from .nodes.observe import observe_node
from .nodes.think import think_node
from .nodes.act import act_node
from .nodes.write import write_node
from .graph import create_graph
from .actions.registry import ActionRegistry
from .actions.executor import ActionExecutor
from memory.store import WeaviateStore
from memory.working_memory import WorkingMemory
from config.settings import settings

class AliceAgent:
    def __init__(self, user_id: str, connection_manager=None):
        self.user_id = user_id
        self.persona = PersonaManager()
        self.user_profile = self._load_user_config()
        self.llm = LLMProvider()
        self.memory_store = WeaviateStore() # In real app, pass config
        self.working_memory = WorkingMemory(user_id=user_id, perception_size=settings.INSTANT_MEMORY_LIMIT)
        
        # Action System
        self.action_registry = ActionRegistry(self.memory_store)
        self.action_executor = ActionExecutor(self.action_registry)
        self.connection_manager = connection_manager # Needed for broadcasting actions

        self.graph = create_graph(self)
        
        self.input_queue = asyncio.Queue()
        self.is_running = False
        self.output_callback: Optional[Callable[[str], Any]] = None
        self.log_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        self.current_task: Optional[asyncio.Task] = None
        self._lifecycle_lock = asyncio.Lock()

    def _load_user_config(self) -> Dict[str, Any]:
        try:
            path = "config/user.json"
            # Handle relative paths
            if not os.path.isabs(path):
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(base_path, path)
            else:
                full_path = path
                
            if os.path.exists(full_path):
                print(f"Loading user config from: {full_path}")
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded user config: {data}")
                    return data
            print(f"User config not found at: {full_path}")
            return {}
        except Exception as e:
            print(f"Error loading user config: {e}")
            return {}

    async def run_observe(self, state: Dict[str, Any]):
        result = await observe_node(state, self.memory_store, self.working_memory, self.llm)
        
        # Broadcast instant memory update
        if self.connection_manager:
            await self.connection_manager.send_event(self.user_id, {
                "type": "agent_state",
                "data": {
                    "instant_memory": list(self.working_memory.instant_memory_queue)
                }
            })
            
        return result

    async def run_think(self, state: Dict[str, Any]):
        # Inject user profile into state for think node
        state['user_profile'] = self.user_profile
        agent_name = self.persona.config.get("basic_info", {}).get("name", "Alice")
        state['agent_name'] = agent_name
        
        result = await think_node(state, self.persona, self.llm, self.action_registry)
        result['agent_name'] = agent_name
        return result

    async def run_act(self, state: Dict[str, Any]):
        # We need connection_manager to broadcast events
        # If it's None, we just skip broadcasting
        if not self.connection_manager:
            # Try to find a way to broadcast or just log
            pass
        return await act_node(state, self.action_executor, self.connection_manager, self.working_memory, self.persona)

    def set_output_callback(self, callback: Callable[[str], Any]):
        self.output_callback = callback

    def set_log_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.log_callback = callback

    async def start(self):
        async with self._lifecycle_lock:
            if self.is_running:
                return
            self.is_running = True
            self.current_task = asyncio.create_task(self._run_loop())
            print(f"Agent {self.user_id} started thinking loop.")

    async def stop(self):
        async with self._lifecycle_lock:
            self.is_running = False
            if self.current_task:
                self.current_task.cancel()
                try:
                    await self.current_task
                except asyncio.CancelledError:
                    pass
                self.current_task = None
            print(f"Agent {self.user_id} stopped.")
        print(f"Agent {self.user_id} stopped.")

    async def on_message(self, message: str):
        """
        Push user message to input queue.
        """
        await self.input_queue.put(message)

    async def _run_loop(self):
        while self.is_running:
            try:
                # Check for new input (non-blocking or with timeout)
                try:
                    user_input = self.input_queue.get_nowait()
                except asyncio.QueueEmpty:
                    user_input = None

                if self.log_callback:
                    await self.log_callback({
                        "type": "cycle_start",
                        "input": user_input
                    })

                # 1. Run the Graph (Observe -> Think)
                agent_name = self.persona.config.get("name", "Alice")
                initial_state = {
                    "input": user_input,
                    "user_id": self.user_id,
                    "user_profile": self.user_profile,
                    "agent_name": agent_name,
                    "persona_prompt": self.persona.get_persona_prompt(self.user_profile),
                    "history_str": self.working_memory.get_context_string(),
                    "perception_queue_str": self.working_memory.get_instant_memory_string(),
                    "memories": [],
                    "thought_data": {},
                    "output": ""
                }
                
                # Run graph
                final_state = await self.graph.ainvoke(initial_state)
                
                # Check if agent wants to speak
                thought_data = final_state.get("thought_data", {})
                action_queue = thought_data.get("action_queue", [])
                
                # Check if 'speak' action was already executed in act_node
                has_spoken = any(action.get("name") == "speak" for action in action_queue)

                if self.log_callback:
                    await self.log_callback({
                        "type": "thought",
                        "content": thought_data
                    })
                    # Persist Thinking Process for history restoration
                    actions = thought_data.get("thinking_pool_actions", {})
                    if actions:
                        process_text = ""
                        for a in actions.get("add", []):
                            process_text += f"▶ Started: {a.get('topic')}\n{a.get('content')}\n"
                        for a in actions.get("continue", []):
                            process_text += f"▷ Continued [{a.get('id')}]: {a.get('new_content')}\n"
                        for pid in actions.get("complete", []):
                            process_text += f"■ Completed [{pid}]\n"
                        
                        if process_text:
                            self.working_memory.add_event("thinking_process", process_text.strip(), data=actions)
                
                # If 'speak' action was executed, we don't need to do anything else here.
                # The act_node has already handled the output and memory persistence.
                if has_spoken:
                     if self.log_callback:
                        await self.log_callback({
                            "type": "action",
                            "content": "Spoke via action."
                        })
                else:
                    # Only if NO speak action was taken, we check if we should log silence.
                    # We no longer use write_node to generate speech to avoid double speaking or extra LLM calls.
                    if self.log_callback:
                        await self.log_callback({
                            "type": "action",
                            "content": "Decided to stay silent."
                        })
                
                # Wait a bit before next thought cycle to prevent tight loop
                # In a real autonomous agent, this might be dynamic.
                await asyncio.sleep(settings.THINKING_INTERVAL) 

            except asyncio.CancelledError:
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error in agent loop: {e}")
                if self.log_callback:
                    await self.log_callback({
                        "type": "error",
                        "content": str(e)
                    })
                await asyncio.sleep(5)
