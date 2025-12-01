from typing import Dict, Any
from ..llm.provider import LLMProvider
from ..persona.manager import PersonaManager
from ..prompts import (
    THINK_NODE_SYSTEM_PROMPT, 
    DEFAULT_SPATIAL_DESC
)
from ..utils import get_chinese_time_desc, USER_SILENT_MSG, DEFAULT_ERROR_RESPONSE
from ..actions.registry import ActionRegistry
from ..memory.metacognition import get_metacognitive_prompt
import json
from datetime import datetime
from config.settings import settings
from ..recorder import recorder

async def think_node(state: Dict[str, Any], persona: PersonaManager, llm: LLMProvider, action_registry: ActionRegistry):
    """
    Reasoning loop. Updates persona state and decides next action.
    """
    # Construct prompt with Persona + Context
    persona_state = persona.get_state()
    memories = state.get("memories", [])
    history = state.get("history_str", "")
    # 队列顺序：由远至近 (Oldest to Newest)
    perception_queue = state.get("perception_queue_str", "")
    current_input = state.get("input")
    user_id = state.get("user_id")
    user_profile = state.get("user_profile")
    
    # Fetch Social State
    social_state = action_registry.memory_store.get_social_state(user_id)
    
    user_name = user_profile.get("name", "用户") if user_profile else "用户"
    input_display = f"'{current_input}'" if current_input else f"（{user_name}沉默）"
    
    time_desc = get_chinese_time_desc()
    spatial_desc = DEFAULT_SPATIAL_DESC

    # Format available actions
    actions_schema = action_registry.get_all_schemas()
    
    def format_actions_compact(actions):
        categories = {}
        for a in actions:
            # Group by category, default to OTHER
            cat = a.get('category', 'OTHER').upper()
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(a)
            
        lines = []
        # Sort categories for consistent ordering
        for cat in sorted(categories.keys()):
            lines.append(f"[{cat}]")
            for a in categories[cat]:
                params = ", ".join(a.get('parameters', {}).keys())
                # Format: name(p1,p2): description
                lines.append(f"{a['name']}({params}): {a['description']}")
        return "\n".join(lines)

    actions_str = format_actions_compact(actions_schema)

    # Format Thinking Pool
    thinking_pool = persona_state['intent'].get('thinking_pool', [])
    thinking_pool_str = json.dumps(thinking_pool, ensure_ascii=False, separators=(',', ':')) if thinking_pool else "（空）"

    latest_perception = state.get("latest_perception", "（无新感知）")

    # Format rules with user_name
    # Use replace instead of format to avoid issues with JSON braces in the rules
    # formatted_rules = INTERACTION_RULES.replace("{user_name}", user_name)

    system_prompt = THINK_NODE_SYSTEM_PROMPT.format(
        persona=persona.get_persona_prompt(user_profile),
        metacognition=get_metacognitive_prompt(user_name),
        available_actions=actions_str,
        user_name=user_name,
        
        time_desc=time_desc,
        spatial_desc=spatial_desc,
        # 队列顺序：由远至近 (Oldest to Newest)
        perception_queue=perception_queue,
        latest_perception=latest_perception,
        emotions=json.dumps(persona_state['emotions'], ensure_ascii=False, separators=(',', ':')),
        desires=json.dumps(persona_state['desires'], ensure_ascii=False, separators=(',', ':')),
        goals=json.dumps(persona_state['intent'], ensure_ascii=False, separators=(',', ':')),
        social_state=json.dumps(social_state, ensure_ascii=False, separators=(',', ':')),
        memories=json.dumps(memories, ensure_ascii=False, separators=(',', ':')),
        thinking_pool=thinking_pool_str
    )
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    response_text = await llm.generate(
        messages, 
        model=settings.THINKING_MODEL, 
        api_base=settings.LLM_API_BASE,
        api_key=settings.LLM_API_KEY,
        # response_format={"type": "json_object"},
        **settings.THINK_MODEL_PARAMS
    )
    
    # Log Thought
    recorder.log_thought(messages, str(response_text), metadata={"user_id": user_id})
    
    if not isinstance(response_text, str):
        print(f"CRITICAL WARNING: response_text is not a string! Type: {type(response_text)}")
        print(f"Value: {response_text}")
        # Attempt to convert to string if possible
        if isinstance(response_text, dict):
             response_text = json.dumps(response_text)
        else:
             response_text = str(response_text)

    # Parse JSON (simple parsing for PoC)
    # In production, use structured output or robust parsing
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_str = response_text[start:end]
        thought_data = json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response_text}")
        # Fallback to empty thought data to avoid crash
        thought_data = {}

    # --- Adapter for New Response Format ---
    
    # 1. Map State Updates
    state_update = thought_data.get("state_update", {})
    if state_update:
        thought_data["emotions_update"] = state_update.get("emotions", {})
        thought_data["desires_update"] = state_update.get("desires", {})
        thought_data["social_state_update"] = state_update.get("social", {})
        thought_data["intent_update"] = state_update.get("intent", {})

    # 2. Map Thinking Process to Pool Actions
    thinking_process = thought_data.get("thinking_process", {})
    if thinking_process:
        pool_ops = thinking_process.get("pool_ops", [])
        thinking_pool_actions = {"add": [], "continue": [], "complete": []}
        
        for op in pool_ops:
            op_type = op.get("op")
            if op_type == "add":
                thinking_pool_actions["add"].append(op)
            elif op_type == "continue":
                thinking_pool_actions["continue"].append(op)
            elif op_type == "complete":
                if "id" in op:
                    thinking_pool_actions["complete"].append(op["id"])
        
        thought_data["thinking_pool_actions"] = thinking_pool_actions
        
        # Also map analysis/plan if needed, or just keep them in thought_data
        thought_data["analysis"] = thinking_process.get("analysis")
        thought_data["plan"] = thinking_process.get("plan")

    # 3. Map Response
    if "response" in thought_data:
        thought_data["response_plan"] = thought_data["response"]

    # --- End Adapter ---

    # Robustness: Handle field name mismatches from LLM
    if "response" in thought_data and "response_plan" not in thought_data:
        thought_data["response_plan"] = thought_data["response"]
    
    if "emotion" in thought_data and "emotions_update" not in thought_data:
        thought_data["emotions_update"] = thought_data["emotion"]
        
    if "desire" in thought_data and "desires_update" not in thought_data:
        thought_data["desires_update"] = thought_data["desire"]

    # Add debug info for logging
    thought_data["_debug"] = {
        "system_prompt": system_prompt,
        "raw_response": response_text
    }
    
    # Update Persona
    intent_update = {
        "thinking_pool_actions": thought_data.get("thinking_pool_actions", {})
    }
    
    # Merge with intent from state_update
    if "intent_update" in thought_data and isinstance(thought_data["intent_update"], dict):
        # Filter out None values to prevent clearing goals accidentally
        valid_updates = {k: v for k, v in thought_data["intent_update"].items() if v is not None}
        intent_update.update(valid_updates)

    # Fallback: Check for direct short_term_goal
    if "short_term_goal" in thought_data and thought_data["short_term_goal"]:
        intent_update["short_term_goal"] = thought_data["short_term_goal"]

    # Debug Log
    print(f"ThinkNode: Updating persona intent with: {json.dumps(intent_update, ensure_ascii=False)}")

    persona.update_state({
        "emotions": thought_data.get("emotions_update", {}),
        "desires": thought_data.get("desires_update", {}),
        "intent": intent_update
    })

    # Update Social State (Persistence)
    social_update = thought_data.get("social_state_update")
    if social_update and isinstance(social_update, dict):
        # Merge with current state to ensure completeness
        new_social_state = social_state.copy()
        new_social_state.update(social_update)
        action_registry.memory_store.update_social_state(user_id, new_social_state)
    
    # Get updated thinking pool to send to frontend
    updated_state = persona.get_state()
    thought_data["thinking_pool"] = updated_state['intent'].get('thinking_pool', [])
    thought_data["life_goal"] = updated_state['intent'].get('life_goal')
    thought_data["long_term_goal"] = updated_state['intent'].get('long_term_goal')
    thought_data["short_term_goal"] = updated_state['intent'].get('short_term_goal') # Explicitly add short_term_goal
    
    state["thought_data"] = thought_data

    return state
