from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
from .manager import manager
import json

router = APIRouter()

import os
from datetime import datetime
from config.settings import settings

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    agent = manager.get_agent(user_id)
    
    # Ensure log directory exists
    log_dir = settings.LOG_DIR_BACKEND
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"agent_{user_id}_{datetime.now().strftime('%Y%m%d')}.log")

    async def send_to_client(data: Dict[str, Any]):
        try:
            if data["type"] == "response_start":
                 await websocket.send_json({"type": "agent_response_start"})
            elif data["type"] == "response_chunk":
                 await websocket.send_json({
                    "type": "agent_stream",
                    "chunk": data["content"]
                })
            elif data["type"] == "response_end":
                 await websocket.send_json({"type": "agent_response_end"})
        except Exception as e:
            print(f"Error sending to client: {e}")

    async def send_log_to_client(log_data: Dict[str, Any]):
        # Write to file
        try:
            with open(log_file, "a") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {json.dumps(log_data)}\n")
        except Exception as e:
            print(f"Error writing log: {e}")

        # Send to WS
        try:
            await websocket.send_json({
                "type": "agent_log",
                "log": log_data
            })
        except Exception as e:
            print(f"Error sending log to client: {e}")

    agent.set_output_callback(send_to_client)
    agent.set_log_callback(send_log_to_client)
    await agent.start()
    
    # Send initial history
    if agent.working_memory.history:
        await websocket.send_json({
            "type": "history_update",
            "history": agent.working_memory.history
        })

    # Send initial agent state
    current_state = agent.persona.get_state()
    frontend_state = {
        "emotions": current_state.get("emotions", {}),
        "desires": current_state.get("desires", {}),
        "goals": current_state.get("intent", {})
    }
    await websocket.send_json({
        "type": "agent_state",
        "data": frontend_state
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_content = message_data.get("content")
                
                if user_content:
                    # Update agent perception
                    await agent.on_message(user_content)
                    
            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON")
                
    except WebSocketDisconnect:
        await agent.stop()
        manager.disconnect(user_id)
