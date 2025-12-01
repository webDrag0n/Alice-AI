from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..websockets.manager import manager

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentGoalsUpdate(BaseModel):
    life_goal: Optional[str] = None
    long_term_goal: Optional[str] = None

@router.put("/{user_id}/goals")
async def update_agent_goals(user_id: str, goals: AgentGoalsUpdate):
    agent = manager.get_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found (is the websocket connected?)")
    
    updates = {"intent": {}}
    if goals.life_goal is not None:
        updates["intent"]["life_goal"] = goals.life_goal
    if goals.long_term_goal is not None:
        updates["intent"]["long_term_goal"] = goals.long_term_goal
    
    agent.persona.update_state(updates)
    
    # Trigger a state update to the frontend via WebSocket
    # We can do this by manually sending the log or just waiting for the next cycle.
    # But for immediate feedback, let's try to push the state.
    # The agent doesn't have a direct "push state" method exposed easily, 
    # but the run loop logs the state.
    # Let's just return success and let the frontend update its local state optimistically 
    # or wait for the next thought cycle.
    # Actually, we can force a log if we want, but it's not strictly necessary if the frontend handles it.
    
    return {"status": "updated", "goals": goals.dict(exclude_unset=True)}

@router.delete("/{user_id}/thinking-pool/{item_id}")
async def delete_thinking_pool_item(user_id: str, item_id: str):
    agent = manager.get_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found (is the websocket connected?)")
    
    current_state = agent.persona.get_state()
    thinking_pool = current_state['intent'].get('thinking_pool', [])
    
    # Filter out the item with the given id
    new_pool = [item for item in thinking_pool if item.get('id') != item_id]
    
    if len(new_pool) == len(thinking_pool):
        raise HTTPException(status_code=404, detail="Thinking pool item not found")
        
    agent.persona.update_state({
        "intent": {
            "thinking_pool": new_pool
        }
    })
    
    return {"status": "deleted", "item_id": item_id}
