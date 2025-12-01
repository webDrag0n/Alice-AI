from typing import Dict, Any, AsyncGenerator
from ..llm.provider import LLMProvider

async def write_node(state: Dict[str, Any], llm: LLMProvider) -> AsyncGenerator[str, None]:
    """
    Generates the final response stream.
    Now it simply streams the response_plan from the think node, 
    treating speaking as a direct output of the thought process.
    """
    thought_data = state.get("thought_data", {})
    plan = thought_data.get("response_plan", "...")
    
    # Handle silence
    if plan == "None" or plan is None:
        return

    # Normalize plan to string to handle various LLM outputs (str, list, dict)
    content_to_stream = ""
    
    if isinstance(plan, str):
        content_to_stream = plan
    elif isinstance(plan, list):
        # If plan is a list (multiple messages), join them
        valid_parts = [str(p) for p in plan if p]
        content_to_stream = "\n".join(valid_parts)
    elif isinstance(plan, dict):
        # If plan is a dict, try to extract text content
        if "content" in plan:
            content_to_stream = str(plan["content"])
        elif "message" in plan:
            content_to_stream = str(plan["message"])
        elif "text" in plan:
            content_to_stream = str(plan["text"])
        else:
            # Fallback: dump json
            import json
            content_to_stream = json.dumps(plan, ensure_ascii=False)
    else:
        content_to_stream = str(plan)

    # Simulate streaming for the frontend
    chunk_size = 5
    for i in range(0, len(content_to_stream), chunk_size):
        yield content_to_stream[i:i+chunk_size]

