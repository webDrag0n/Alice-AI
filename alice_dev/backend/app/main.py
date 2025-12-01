from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .websockets import connection
from .api import memories, agent

app = FastAPI(title="Alice AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router)
app.include_router(memories.router)
app.include_router(agent.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
