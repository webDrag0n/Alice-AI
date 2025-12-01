from typing import Dict, Any, TYPE_CHECKING
import asyncio
from ..actions.executor import ActionExecutor
from ..actions.registry import ActionRegistry
from memory.store import WeaviateStore
from memory.working_memory import WorkingMemory
from ..utils import SYSTEM_RECALL_MSG

if TYPE_CHECKING:
    from app.websockets.manager import ConnectionManager

from ..persona.manager import PersonaManager

async def act_node(state: Dict[str, Any], action_executor: ActionExecutor, connection_manager: "ConnectionManager", working_memory: WorkingMemory, persona: PersonaManager = None):
    """
    Executes the actions decided by the Think node.
    """
    thought_data = state.get("thought_data", {})
    raw_action_queue = thought_data.get("action_queue", [])
    user_id = state.get("user_id")
    
    # Enrich with status and ensure list copy
    action_queue = []
    for item in raw_action_queue:
        # Create a copy to avoid modifying the original thought data in place if that matters, 
        # but mainly to add status without affecting other things if shared.
        new_item = item.copy()
        new_item["status"] = "pending"
        # Ensure parameters is a dict to prevent frontend crashes
        if "parameters" not in new_item or new_item["parameters"] is None:
            new_item["parameters"] = {}
        action_queue.append(new_item)
    
    # 0. Broadcast Full Agent State (Sync with Frontend)
    # This ensures that even if no actions are taken, the frontend receives the latest
    # emotions, desires, and goals (including short_term_goal) updated by the Think node.
    if connection_manager and user_id and persona:
        current_state = persona.get_state()
        # Map to frontend expected format
        frontend_state = {
            "emotions": current_state.get("emotions", {}),
            "desires": current_state.get("desires", {}),
            "goals": current_state.get("intent", {})
        }
        await connection_manager.send_event(user_id, {
            "type": "agent_state",
            "data": frontend_state
        })

    # 1. Broadcast Action Queue (Start)
    if connection_manager and user_id and action_queue:
        await connection_manager.send_event(user_id, {
            "type": "action_queue_update",
            "data": action_queue
        })

    if not action_queue:
        return state

    # Execute actions sequentially
    results = []
    
    # Inject persona into state for actions that need it (like Think)
    if persona:
        state["persona"] = persona
    
    # Inject working_memory into state for actions that need it (like MinecraftPerception)
    if working_memory:
        state["working_memory"] = working_memory
    
    for i, item in enumerate(action_queue):
        # Update status to executing
        item["status"] = "executing"
        if connection_manager and user_id:
            await connection_manager.send_event(user_id, {
                "type": "action_queue_update",
                "data": action_queue
            })
        
        # Add delay for visual effect
        await asyncio.sleep(0.5)
            
        name = item.get("name")
        params = item.get("parameters", {})
        
        # Execute using registry
        action = action_executor.registry.get_action(name)
        res = {}
        
        if action:
            try:
                res = await action.execute(state, **params)
                item["status"] = "completed"
                item["result"] = res
            except Exception as e:
                res = {"error": f"Failed to execute {name}: {str(e)}"}
                item["status"] = "failed"
                item["result"] = res
        else:
            res = {"error": f"Action {name} not found"}
            item["status"] = "failed"
            item["result"] = res
            
        results.append(res)

        # Add to perception queue so agent knows what it did
        action_name = name
        agent_name = state.get("agent_name", "Alice")
        
        if "error" not in res:
            # Include result summary in perception
            result_summary = res.get("message", "")
            
            if "data" in res:
                data = res["data"]
                
                # 1. Handle List Data (Recall/Associate)
                if isinstance(data, list):
                    # Try to extract content from memory objects
                    mem_texts = []
                    for item in data:
                        if hasattr(item, 'properties'):
                            mem_texts.append(item.properties.get("content", ""))
                        elif isinstance(item, dict):
                            mem_texts.append(item.get("content", str(item)))
                        else:
                            mem_texts.append(str(item))
                    
                    if mem_texts:
                        # Limit to top 3 for summary
                        summary_text = "; ".join(mem_texts[:3])
                        if len(mem_texts) > 3:
                            summary_text += f" ... ({len(mem_texts)-3} more)"
                        result_summary += f"\n内容: {summary_text}"

                # 2. Handle String Data (Memorize)
                elif isinstance(data, str):
                     if action_name == "memorize":
                         result_summary += f"\n内容: {data}"

                # 3. Handle Dict Data (Web/Code)
                elif isinstance(data, dict):
                    # Special handling for web browse to include title
                    if "title" in data:
                        result_summary += f" (Title: {data['title']})"
                    
                    # Special handling for web browse to include extracted links
                    if "extracted_links" in data and data["extracted_links"]:
                        links_str = "\n".join([f"- {link['text']}: {link['url']}" for link in data["extracted_links"][:5]]) # Limit to 5 for brevity in memory
                        result_summary += f"\n发现链接:\n{links_str}"

                    # Special handling for web browse to include content
                    if "content" in data and data["content"]:
                        # Limit content length to avoid overwhelming the context, though web.py already truncates to 2000
                        content_preview = data["content"][:1000] + "..." if len(data["content"]) > 1000 else data["content"]
                        result_summary += f"\n页面内容摘要:\n{content_preview}"
                    
                    # Special handling for code execution (Python/Bash) to include full output
                    if "output" in data and data["output"]:
                        # Avoid duplicating if message already contains it (simple check)
                        if str(data["output"])[:50] not in result_summary:
                            result_summary += f"\n执行输出:\n{data['output']}"
                    
                    if "error" in data and data["error"]:
                        result_summary += f"\n执行错误:\n{data['error']}"
            
            # --- New Perception Logic ---
            # 1. Action Itself -> Instant Memory (What I did)
            # Skip for speak/think as they are internal/output only or handled elsewhere
            if not action_name.startswith("think_") and action_name != "speak":
                # Construct a natural language description of the action
                # We can use the 'message' from the result which is usually "Alice is doing X..."
                # Or construct it from name and params.
                # The 'message' field in result is usually good: "Alice 正在回忆..."
                action_desc = res.get("message", f"我执行了 {action_name}")
                
                # For memory actions, use the full result summary (which includes content) 
                # so the agent immediately knows what it recalled/memorized without checking senses
                if action_name in ["recall", "associate", "memorize"]:
                    action_desc = result_summary

                working_memory.add_instant_memory(f"[自我行为] {action_desc}")

            # 2. Action Result -> Senses (What happened)
            # Skip for speak/think
            if not action_name.startswith("think_") and action_name != "speak":
                # Determine target sense based on action type
                target_senses = ["sight"] # Default
                
                if action_name in ["recall", "associate", "memorize", "think_add", "think_update", "think_complete"]:
                    target_senses = ["mind"]
                elif action_name in ["listen"]:
                    target_senses = ["hearing"]
                elif action_name in ["daze"]:
                    target_senses = ["mind", "body"] # Daze affects energy (body) and mind
                elif action_name in ["run_python", "run_bash", "browse_web"]:
                    target_senses = ["sight"] # Code output and web pages are visual
                
                # Write result to senses
                for sense in target_senses:
                    working_memory.write_to_sense(sense, f"动作 {action_name} 的反馈: {result_summary}")

        # else:
        #      # Error case
        #      working_memory.add_instant_memory(f"[自我行为] 尝试执行 {action_name} 但失败了")
        #      working_memory.write_to_sense("sight", f"错误信息: {res.get('error')}")

        # 2. Send to Frontend
        if connection_manager and user_id:
            if name == "speak":
                 # Send as speech
                 content = res.get("data", "")
                 
                 # Only record and send if there's actual content and no error
                 if content and "error" not in res:
                     # 1. Record in memory FIRST to ensure persistence
                     working_memory.add_message("assistant", content, actionData=res)
                     
                     # 2. Send to Frontend
                     await connection_manager.send_event(user_id, {"type": "agent_response_start"})
                     await connection_manager.send_event(user_id, {
                        "type": "agent_stream",
                        "chunk": content
                     })
                     await connection_manager.send_event(user_id, {"type": "agent_response_end"})
                 elif "error" in res:
                     # Handle error case
                     error_msg = res.get("error")
                     working_memory.add_event("action_error", f"说话失败: {error_msg}", data=res)
                     await connection_manager.send_event(user_id, {
                        "type": "agent_action",
                        "data": res
                     })

            else:
                # Send action result
                if "message" in res:
                    # Persist action event FIRST
                    working_memory.add_event("action", res.get("message", ""), data=res)
                    
                    await connection_manager.send_event(user_id, {
                        "type": "agent_action",
                        "data": res
                    })
            
            # Send updated queue (with completed/failed status)
            await connection_manager.send_event(user_id, {
                "type": "action_queue_update",
                "data": action_queue
            })
            
        # 3. Update State (if applicable)
        if "state_update" in res:
            updates = res["state_update"]
            # Handle specific updates like working memory
            if "working_memory_append" in updates:
                current_memories = state.get("memories", [])
                new_mems = updates["working_memory_append"]
                # Update current state memories (for Write node if it uses them)
                state["memories"] = current_memories + [m.properties for m in new_mems if hasattr(m, 'properties')]
                
                # Persist to WorkingMemory for next turn
                # We add a system note so the agent knows what it recalled
                # Extract content from memories
                mem_contents = [m.properties.get("content", "") for m in new_mems if hasattr(m, 'properties')]
                if mem_contents:
                    note = SYSTEM_RECALL_MSG.format('; '.join(mem_contents))
                    # Also add to instant memory for immediate awareness
                    working_memory.add_instant_memory(f"[记忆检索] {note}")
                    # working_memory.add_message("system", note) # Optional: Keep in history if needed, but instant memory is better for "thought" context

            if "emotions" in updates:
                # This is tricky because PersonaManager manages emotions.
                # We might need to pass PersonaManager to Act node too, or return updates to be applied.
                # For now, let's just log it.
                pass
            
            # Broadcast generic state update if present (e.g. thinking_pool from Think action)
            # We filter out internal keys like working_memory_append
            broadcast_updates = {k: v for k, v in updates.items() if k not in ["working_memory_append"]}
            if broadcast_updates and connection_manager and user_id:
                 # If we have persona, we might want to get the full updated state to be safe, 
                 # or just trust the partial update.
                 # For thinking_pool, the Think action returns the full pool in 'intent' -> 'thinking_pool' structure if we map it right.
                 # But Think action returns {"intent": {"thinking_pool": ...}} in state_update?
                 # Let's check Think action implementation.
                 # It does: persona.update_state({"intent": {"thinking_pool": current_pool}})
                 # But it doesn't return that in state_update in my previous edit. I need to fix Think action.
                 
                 # Assuming Think action returns proper structure for frontend:
                 # Frontend expects agent_state event with data matching AgentState type.
                 # AgentState has goals: { thinking_pool: ... }
                 # So we need to map intent -> goals.
                 
                 frontend_update = {}
                 if "intent" in broadcast_updates:
                     # CRITICAL FIX: Merge with existing goals to avoid overwriting short_term_goal with None
                     # if the action update only contains thinking_pool
                     if persona:
                         current_intent = persona.get_state()["intent"]
                         # We use the current full intent state, which includes the short_term_goal set by Think node
                         frontend_update["goals"] = current_intent
                     else:
                         frontend_update["goals"] = broadcast_updates["intent"]
                 
                 if "emotions" in broadcast_updates:
                     frontend_update["emotions"] = broadcast_updates["emotions"]
                     
                 if "desires" in broadcast_updates:
                     frontend_update["desires"] = broadcast_updates["desires"]
                 
                 if frontend_update:
                    await connection_manager.send_event(user_id, {
                        "type": "agent_state",
                        "data": frontend_update
                    })

    state["action_results"] = results
    return state