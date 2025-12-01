from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from memory.store import WeaviateStore
from config.settings import settings
from soul.actions.registry import ActionRegistry
from soul.memory.metacognition import METACOGNITIVE_MEMORIES
# Import manager using relative path to avoid circular or path issues
# Assuming this file is in backend/app/api/
from ..websockets.manager import manager

router = APIRouter(prefix="/memories", tags=["memories"])

class MemoryCreate(BaseModel):
    content: str
    user_id: str
    type: str = "episodic"
    importance: float = 0.5

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    type: Optional[str] = None
    importance: Optional[float] = None

class MemoryResponse(BaseModel):
    id: str
    content: str
    type: str
    user_id: str
    timestamp: str
    importance: float
    distance: Optional[float] = None
    tags: Optional[List[str]] = []
    attributes: Optional[str] = "{}"

def get_store():
    # In a real app, use dependency injection or a singleton manager
    return WeaviateStore(url=settings.WEAVIATE_URL)

@router.get("/actions")
async def get_actions(user_id: str):
    agent = manager.get_agent(user_id)
    if agent:
        return agent.action_registry.get_all_schemas()
    else:
        # Fallback: create a temporary registry
        # We pass None as memory_store because we only need schemas
        registry = ActionRegistry(None)
        return registry.get_all_schemas()

@router.get("/metacognition")
async def get_metacognition():
    return METACOGNITIVE_MEMORIES

@router.get("/social_state/{user_id}")
async def get_social_state(user_id: str):
    store = get_store()
    try:
        return store.get_social_state(user_id)
    finally:
        store.close()

@router.get("/", response_model=List[MemoryResponse])
async def get_memories(user_id: str, limit: int = 50, query: Optional[str] = None, type: Optional[str] = None):
    store = get_store()
    try:
        if query:
            results = store.search_memories(query, user_id, limit, memory_type=type)
        else:
            # If type is specified, we need a way to filter by type in get_all_memories
            # The current get_all_memories doesn't support type filtering, let's use search with empty query or update store
            # For now, let's just use search with empty query if type is present, or update get_all_memories
            # Actually, let's just update get_all_memories in store.py if needed, but for now search_memories handles type.
            # If query is None but type is set, we can't use search_memories easily without a query.
            # Let's assume we use search_memories with "*" or similar if supported, or just fetch all and filter (inefficient).
            # Better: Update store.py to support type filter in get_all_memories.
            # For this PoC, let's just use search_memories with a generic query if type is set, or just fetch all.
            if type:
                 results = store.search_memories("", user_id, limit, memory_type=type)
            else:
                 results = store.get_all_memories(user_id, limit)
        return results
    finally:
        store.close()

@router.post("/")
async def create_memory(memory: MemoryCreate):
    store = get_store()
    try:
        store.add_memory(memory.content, memory.user_id, memory.type, memory.importance)
        return {"status": "created"}
    finally:
        store.close()

@router.put("/{memory_id}")
async def update_memory(memory_id: str, memory: MemoryUpdate):
    store = get_store()
    try:
        updates = {k: v for k, v in memory.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        store.update_memory(memory_id, updates)
        return {"status": "updated"}
    finally:
        store.close()

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    store = get_store()
    try:
        store.delete_memory(memory_id)
        return {"status": "deleted"}
    finally:
        store.close()
