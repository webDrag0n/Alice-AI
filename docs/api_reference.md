# API & WebSocket Reference

## WebSocket Protocol

**Endpoint**: `ws://<host>:8000/ws/{user_id}`

The WebSocket connection is the primary channel for real-time interaction.

### Client -> Server Messages

**User Message**
```json
{
  "type": "user_message",
  "content": "Hello Alice!"
}
```

### Server -> Client Messages

**1. Stream Chunk** (Real-time LLM output)
```json
{
  "type": "agent_stream",
  "chunk": "Hello "
}
```

**2. Stream End**
```json
{
  "type": "agent_stream_end"
}
```

**3. Action Queue Update**
Sent whenever the status of the action queue changes.
```json
{
  "type": "action_queue_update",
  "data": [
    {
      "name": "recall",
      "parameters": { "query": "user name" },
      "status": "executing" // pending, executing, completed, failed
    }
  ]
}
```

**4. Agent Action Result**
Sent when an action completes.
```json
{
  "type": "agent_action",
  "data": {
    "event": "recall",
    "message": "I recall that your name is Bob.",
    "data": [...]
  }
}
```

**5. Agent State Update**
Sent to update the frontend dashboard (Emotions, Goals).
```json
{
  "type": "agent_state",
  "data": {
    "emotions": { "joy": 0.8 },
    "goals": { "short_term_goal": "..." }
  }
}
```

## HTTP API Endpoints

**Base URL**: `http://<host>:8000`

### General

- `GET /health`: Check system health.
- `GET /`: Root endpoint.

### Memories

- `GET /api/memories/`: Retrieve memories for a user.
- `POST /api/memories/`: Manually create a memory.
- `GET /api/memories/social_state/{user_id}`: Get the social relationship state.

### Agent Management

- `POST /api/reset/{user_id}`: Reset the agent's memory and state for a specific user.

## Data Models

### Memory Item
```json
{
  "content": "User likes coding.",
  "type": "episodic",
  "user_id": "user123",
  "importance": 0.8,
  "timestamp": "2023-10-01T12:00:00Z"
}
```

### Persona State
```json
{
  "emotions": { "joy": 0.5, "anger": 0.0, ... },
  "desires": { "curiosity": 0.8, ... },
  "intent": {
    "life_goal": "...",
    "thinking_pool": [...]
  }
}
```
