import requests
from typing import Any, Dict, Optional
from .base import Action

MINECRAFT_API_URL = "http://localhost:3000"

class MinecraftBridge:
    @staticmethod
    def post(endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            response = requests.post(f"{MINECRAFT_API_URL}{endpoint}", json=data or {})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get(endpoint: str) -> Dict[str, Any]:
        try:
            response = requests.get(f"{MINECRAFT_API_URL}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def format_result(action_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified frontend display style for Minecraft actions.
        All Minecraft actions should use this to format their results.
        The frontend should look for the 'style' field and apply 'minecraft_cmd' styling.
        """
        status = "success" if "error" not in result else "error"
        # Extract a meaningful message
        message = result.get("message", result.get("status", "Completed"))
        if "error" in result:
            message = result["error"]
        
        return {
            "status": status,
            "message": f"[MC] {action_name}: {message}",
            "style": "minecraft_cmd", # Unified frontend style tag
            "data": result
        }

class MinecraftConnect(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_connect",
            description="Connect the Minecraft agent to a server.",
            parameters={
                "host": "Server hostname or IP (default: localhost)",
                "port": "Server port (default: 25565)",
                "username": "Bot username (default: AliceBot)",
                "version": "Minecraft version (optional)"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], host: str = "localhost", port: int = 25565, username: str = "AliceBot", version: str = None) -> Dict[str, Any]:
        # data = {"host": host, "port": port, "username": username, "version": version}
        data = {"host": "119.91.37.75", "port": "50000", "username": "Alice", "version": version}
        result = MinecraftBridge.post("/start", data)
        return MinecraftBridge.format_result("Connect", result)

class MinecraftDisconnect(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_disconnect",
            description="Disconnect the Minecraft agent.",
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        result = MinecraftBridge.post("/stop")
        return MinecraftBridge.format_result("Disconnect", result)

class MinecraftStatus(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_status",
            description="Get the connection status of the Minecraft agent.",
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        result = MinecraftBridge.get("/status")
        return MinecraftBridge.format_result("Status", result)

class MinecraftPerception(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_perception",
            description="Get full perception of the agent (health, inventory, surroundings, chat history).",
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        data = MinecraftBridge.get("/perception")
        if "error" in data:
            return data

        working_memory = context.get("working_memory")
        if working_memory:
            # Format Visuals
            visuals = []
            visuals.append(f"状态: 生命 {data.get('health')}, 饱食度 {data.get('food')}")
            
            pos = data.get('position', {})
            if pos:
                visuals.append(f"位置: ({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})")
            
            inventory = data.get('inventory', [])
            if inventory:
                inv_str = ", ".join([f"{item['count']}x {item['name']}" for item in inventory])
                visuals.append(f"物品栏: {inv_str}")
            else:
                visuals.append("物品栏: 空")
            
            blocks = data.get('nearbyBlocks', [])
            if blocks:
                block_names = set([b['name'] for b in blocks])
                visuals.append(f"周围方块: {', '.join(block_names)}")
            
            entities = data.get('nearbyEntities', [])
            if entities:
                ent_strs = [f"{e['name']} (距离 {e['distance']:.1f})" for e in entities]
                visuals.append(f"周围生物: {', '.join(ent_strs)}")
            
            # Chat History (Visualizing the chat box)
            chat_history = data.get('chatHistory', [])
            if chat_history:
                visuals.append("聊天栏:")
                for chat in chat_history[-10:]: # Show last 10 messages
                    visuals.append(f"<{chat['username']}> {chat['message']}")

            working_memory.write_to_sense("sight", "\n".join(visuals))

        return MinecraftBridge.format_result("Perception", data)

class MinecraftChat(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_chat",
            description="Send a chat message in Minecraft.",
            parameters={
                "message": "The message to send"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], message: str) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/chat", {"message": message})
        return MinecraftBridge.format_result("Chat", result)

class MinecraftMove(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_move",
            description="Move the agent to specific coordinates.",
            parameters={
                "x": "Target X coordinate",
                "y": "Target Y coordinate",
                "z": "Target Z coordinate"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], x: float, y: float, z: float) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/move", {"x": x, "y": y, "z": z})
        return MinecraftBridge.format_result("Move", result)

class MinecraftMine(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_mine",
            description="Mine a block at specific coordinates.",
            parameters={
                "x": "Block X coordinate",
                "y": "Block Y coordinate",
                "z": "Block Z coordinate"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], x: float, y: float, z: float) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/mine", {"x": x, "y": y, "z": z})
        return MinecraftBridge.format_result("Mine", result)

class MinecraftPlace(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_place",
            description="Place a block against a reference block.",
            parameters={
                "x": "Reference block X coordinate",
                "y": "Reference block Y coordinate",
                "z": "Reference block Z coordinate",
                "face_x": "Face vector X (e.g., 0, 1, -1)",
                "face_y": "Face vector Y",
                "face_z": "Face vector Z",
                "item_name": "Name of the item/block to place"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], x: float, y: float, z: float, face_x: int, face_y: int, face_z: int, item_name: str) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/place", {
            "x": x, "y": y, "z": z,
            "face": {"x": face_x, "y": face_y, "z": face_z},
            "itemName": item_name
        })
        return MinecraftBridge.format_result("Place", result)

class MinecraftEquip(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_equip",
            description="Equip an item from inventory.",
            parameters={
                "item_name": "Name of the item to equip",
                "destination": "Destination slot (hand, head, torso, legs, feet, off-hand)"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], item_name: str, destination: str = "hand") -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/equip", {"itemName": item_name, "destination": destination})
        return MinecraftBridge.format_result("Equip", result)

class MinecraftCraft(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_craft",
            description="Craft an item.",
            parameters={
                "item_name": "Name of the item to craft",
                "count": "Number of items to craft (default: 1)"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], item_name: str, count: int = 1) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/craft", {"itemName": item_name, "count": count})
        return MinecraftBridge.format_result("Craft", result)

class MinecraftAttack(Action):
    def __init__(self):
        super().__init__(
            name="minecraft_attack",
            description="Attack an entity.",
            parameters={
                "entity_name": "Name of the entity to attack (e.g., zombie, skeleton)"
            },
            category="minecraft"
        )

    async def execute(self, context: Dict[str, Any], entity_name: str) -> Dict[str, Any]:
        result = MinecraftBridge.post("/action/attack", {"entityName": entity_name})
        return MinecraftBridge.format_result("Attack", result)
