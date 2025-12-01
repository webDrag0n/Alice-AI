# Minecraft Integration

Alice AI includes a standalone Minecraft Agent module that allows Alice to inhabit a Minecraft bot body.

## Overview

The Minecraft integration consists of two parts:
1.  **Minecraft Agent Service (`minecraft_agent/`)**: A Node.js application using `mineflayer` that connects to a Minecraft server and exposes an HTTP API.
2.  **Alice Soul Actions (`soul/actions/minecraft.py`)**: Python actions within the Alice Core that call the Minecraft Agent Service API.

## Setup

### 1. Start the Minecraft Agent Service

The service is located in the root `minecraft_agent` directory (outside `alice_dev`).

```bash
cd minecraft_agent
npm install
npm start
```
The service will listen on port **3000**.

### 2. Configure Alice Core

Ensure the Alice Core (Backend) can reach the Minecraft Agent Service. By default, it expects `http://localhost:3000`.

## Usage

Once both services are running, you can ask Alice to perform Minecraft tasks.

**Example Commands:**
- "Connect to the local Minecraft server." -> Triggers `MinecraftConnect`
- "Look around." -> Triggers `MinecraftPerception`
- "Mine that wood block." -> Triggers `MinecraftMine`
- "Build a small house." -> Triggers complex planning and multiple `MinecraftPlace` actions.

## API Reference (Minecraft Service)

The Node.js service exposes the following endpoints:

### Management
- `POST /start`: Connect bot to server.
- `POST /stop`: Disconnect bot.
- `GET /status`: Check connection status.

### Perception
- `GET /perception`: Get full state (health, inventory, surroundings).
- `GET /surroundings`: Get nearby blocks.

### Actions
- `POST /action/chat`: Send chat message.
- `POST /action/move`: Pathfind to coordinates.
- `POST /action/mine`: Dig a block.
- `POST /action/place`: Place a block.
- `POST /action/craft`: Craft items.
- `POST /action/attack`: Attack entities.
