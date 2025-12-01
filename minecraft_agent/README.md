# Minecraft Agent Interface

This is a standalone Node.js application that acts as a middle layer between the Alice AI system and a Minecraft server using `mineflayer`.

## Installation

1. Navigate to this directory:
   ```bash
   cd minecraft_agent
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## Usage

Start the server:
```bash
npm start
```

The server listens on port 3000 by default.

## API Endpoints

### Management
- `POST /start`: Connect the bot to a server. Body: `{ "host": "localhost", "port": 25565, "username": "AliceBot", "version": "1.20.1" }`
- `POST /stop`: Disconnect the bot.
- `GET /status`: Get connection status.

### Perception
- `GET /perception`: Get full agent state (health, food, inventory, surroundings).
- `GET /inventory`: Get inventory items.
- `GET /surroundings`: Get nearby blocks.

### Actions
- `POST /action/chat`: Send chat message. Body: `{ "message": "Hello" }`
- `POST /action/move`: Move to coordinates. Body: `{ "x": 100, "y": 64, "z": 100 }`
- `POST /action/mine`: Mine a block. Body: `{ "x": 100, "y": 64, "z": 100 }`
- `POST /action/place`: Place a block. Body: `{ "x": 100, "y": 64, "z": 100, "face": { "x": 0, "y": 1, "z": 0 }, "itemName": "dirt" }`
- `POST /action/equip`: Equip an item. Body: `{ "itemName": "sword", "destination": "hand" }`
- `POST /action/craft`: Craft an item. Body: `{ "itemName": "stick", "count": 4 }`
- `POST /action/attack`: Attack an entity. Body: `{ "entityName": "zombie" }`
