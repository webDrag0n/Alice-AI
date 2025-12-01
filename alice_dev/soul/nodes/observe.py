from typing import Dict, Any
import json
from ..persona.manager import PersonaManager
from memory.store import WeaviateStore
from memory.working_memory import WorkingMemory
from ..llm.provider import LLMProvider
from config.settings import settings
from ..recorder import recorder
from ..prompts import PERCEPTION_SYSTEM_PROMPT
from ..actions.innate import Associate, Recall

async def observe_node(state: Dict[str, Any], memory_store: WeaviateStore, working_memory: WorkingMemory, llm: LLMProvider):
    """
    Process input, update working memory, retrieve long-term memory.
    Also runs the Perception Model to summarize raw buffer into Instant Memory.
    """
    user_input = state.get("input")
    user_id = state.get("user_id")
    user_profile = state.get("user_profile", {})
    # print(f"Observe Node - User Profile: {user_profile}")
    user_name = user_profile.get("name", "User")
    agent_name = state.get("agent_name", "Alice")
    persona_prompt = state.get("persona_prompt", "")
    
    # 1. Handle User Input (Add to Buffer & History)
    if user_input:
        # Use "user" as role for consistency, but store name for display/context
        working_memory.add_message("user", user_input, name=user_name)
        # Add to Hearing sense
        working_memory.write_to_sense("hearing", f"听到{user_name}说: {user_input}")
        
        # Note: We no longer trigger Associate here directly. 
        # It is now handled by the Perception Model's JSON output.

    # 2. Process Senses (Summarize into Instant Memory)
    senses_data = working_memory.read_and_clear_senses()
    
    # 强制活跃模式：即使没有新的感官输入，也进行感知处理，以维持意识流
    if not senses_data and settings.CONTINUOUS_THINKING:
        senses_data = {
            "environment": ["没有任何引起注意的事物"]
        }

    if senses_data:
        # Construct prompt for Perception Model
        senses_text = ""
        for sense, lines in senses_data.items():
            senses_text += f"\n[{sense.upper()}]\n" + "\n".join([f"- {line}" for line in lines])

        system_prompt = PERCEPTION_SYSTEM_PROMPT.format(
            persona_prompt=persona_prompt,
            agent_name=agent_name,
            user_name=user_name
        )

        user_prompt = f"""
        感知到的信息:
        {senses_text}
        
        请输出 JSON 格式的分析结果：
        """
        
        messages = [{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}]
        
        response_text = await llm.generate(
            messages, 
            model=settings.PERCEPTION_MODEL,
            api_base=settings.PERCEPTION_API_BASE,
            api_key=settings.PERCEPTION_API_KEY,
            response_format={"type": "json_object"},
            **settings.PERCEPTION_MODEL_PARAMS
        )
        
        # Log Perception
        recorder.log_perception(messages, response_text, metadata={"user_id": user_id})
        
        try:
            perception_result = json.loads(response_text)
            summary = perception_result.get("summary", "")
            association_params = perception_result.get("association_params")
            recall_params = perception_result.get("recall_params")
            
            # 2.1 Handle Summary
            if summary and summary.strip():
                working_memory.add_instant_memory(summary.strip())
            
            # 2.2 Handle Association
            if association_params and "concept" in association_params:
                concept = association_params["concept"]
                if concept:
                    associate_action = Associate(memory_store)
                    action_context = {"user_id": user_id, "agent_name": agent_name}
                    result = await associate_action.execute(action_context, concept=concept)
                    
                    # Update state memories
                    current_memories = state.get("memories", [])
                    new_memories = result.get("data", [])
                    # Merge and deduplicate could be complex, here we just append or replace
                    # For simplicity, let's extend the list
                    state["memories"] = current_memories + new_memories
                    
                    if result.get("message"):
                        working_memory.add_instant_memory(f"[潜意识联想] {result.get('message')}")

            # 2.3 Handle Recall
            if recall_params and "query" in recall_params:
                query = recall_params["query"]
                if query:
                    recall_action = Recall(memory_store)
                    action_context = {"user_id": user_id, "agent_name": agent_name}
                    result = await recall_action.execute(action_context, query=query)
                    
                    # Update state memories
                    current_memories = state.get("memories", [])
                    new_memories = result.get("data", [])
                    state["memories"] = current_memories + new_memories
                    
                    if result.get("message"):
                        working_memory.add_instant_memory(f"[潜意识回忆] {result.get('message')}")

        except json.JSONDecodeError:
            print(f"Perception Model JSON Error: {response_text}")
            # Fallback: treat whole text as summary if not JSON
            working_memory.add_instant_memory(response_text.strip())
        except Exception as e:
            print(f"Perception Logic Error: {e}")
            # Fallback
            for sense, lines in senses_data.items():
                for line in lines:
                    working_memory.add_instant_memory(f"[{sense}] {line}")

    #     for sense, lines in senses_data.items():
    #         for line in lines:
    #             working_memory.add_instant_memory(f"[{sense}] {line}")
    #     # working_memory.clear_buffer() # No longer needed as we read_and_clear_senses

    # 3. Update State for Think Node
    state["perception_queue_str"] = working_memory.get_instant_memory_string()
    # Pass the latest perception summary (if any) to the state so Think node can highlight it
    # If summary was generated, it's the last item in the queue.
    # If fallback was used, it's the last few items.
    # For simplicity, we just let Think node look at the queue, but we can flag "new_input"
    state["latest_perception"] = working_memory.instant_memory_queue[-1] if working_memory.instant_memory_queue else "（无新感知）"
    
    return state
