import json
from typing import Dict, Any
from fastapi import WebSocket
from soul.agent import AliceAgent

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, AliceAgent] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        if user_id not in self.agents:
            # Pass self as connection_manager
            self.agents[user_id] = AliceAgent(user_id, connection_manager=self)
            print(f"Initialized new agent for user {user_id}")
        
        # Send history to the newly connected user
        agent = self.agents[user_id]
        history = agent.working_memory.history
        if history:
            await self.send_event(user_id, {
                "type": "history_update",
                "history": history
            })

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        # We might want to keep the agent alive for a bit, or persist state.

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: Dict[str, Any]):
        # This method name is misleading if it's for a specific user, 
        # but act_node calls it 'broadcast'. 
        # Since AliceAgent is tied to a user, we might need to know WHICH user.
        # But act_node calls it on the manager instance passed to the agent.
        # The agent instance knows the user_id, but act_node is a function.
        # We should probably have a method send_to_user(user_id, data).
        pass

    async def send_event(self, user_id: str, event_data: Dict[str, Any]):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(event_data)

    def get_agent(self, user_id: str) -> AliceAgent:
        return self.agents.get(user_id)

manager = ConnectionManager()
