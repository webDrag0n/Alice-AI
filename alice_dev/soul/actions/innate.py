import asyncio
from typing import Any, Dict, List
from .base import Action
from memory.store import WeaviateStore

class Daze(Action):
    def __init__(self):
        super().__init__(
            name="daze",
            description="发呆。当你无事可做或想放松时使用。会恢复少量能量。",
            parameters={"duration": "发呆持续的时间（秒）"},
            category="rest"
        )

    async def execute(self, context: Dict[str, Any], duration: int = 5, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        await asyncio.sleep(min(int(duration), 5)) # Limit real sleep
        return {
            "event": "daze",
            "message": f"{agent_name} 正在发呆 ({duration}s)...",
            "state_update": {"emotions": {"energy": 5}} # Example update
        }

class Speak(Action):
    def __init__(self):
        super().__init__(
            name="speak",
            description="说话。用语言交流。",
            parameters={"content": "要说的话"},
            category="communication"
        )

    async def execute(self, context: Dict[str, Any], content: str, **kwargs) -> Dict[str, Any]:
        return {
            "event": "speak",
            "message": content,
            "data": content
        }

class Recall(Action):
    def __init__(self, memory_store: WeaviateStore):
        self.memory_store = memory_store
        super().__init__(
            name="recall",
            description="回忆。主动搜索特定记忆。用于需要精确信息的场景。",
            parameters={"query": "搜索关键词", "limit": "返回数量"},
            category="memory"
        )

    async def execute(self, context: Dict[str, Any], query: str, limit: int = 3, **kwargs) -> Dict[str, Any]:
        user_id = context.get("user_id")
        agent_name = context.get("agent_name", "Alice")
        # Use search_memories instead of search
        results = self.memory_store.search_memories(query, user_id, limit=int(limit))
        return {
            "event": "recall",
            "message": f"{agent_name} 正在回忆关于 '{query}' 的事情...",
            "data": results,
            "state_update": {"working_memory_append": results} 
        }

class Associate(Action):
    def __init__(self, memory_store: WeaviateStore):
        self.memory_store = memory_store
        super().__init__(
            name="associate",
            description="联想。发散性思维，搜索相关但不一定精确匹配的记忆。用于寻找灵感。",
            parameters={"concept": "联想的核心概念"},
            category="memory"
        )

    async def execute(self, context: Dict[str, Any], concept: str, **kwargs) -> Dict[str, Any]:
        user_id = context.get("user_id")
        agent_name = context.get("agent_name", "Alice")
        # Use search_memories instead of search
        results = self.memory_store.search_memories(concept, user_id, limit=5) 
        return {
            "event": "associate",
            "message": f"{agent_name} 正在由 '{concept}' 展开联想...",
            "data": results,
            "state_update": {"working_memory_append": results}
        }

class Memorize(Action):
    def __init__(self, memory_store: WeaviateStore):
        self.memory_store = memory_store
        super().__init__(
            name="memorize",
            description="记忆。将当前发生的事件、对话或体验存入情景记忆(Episodic)。用于记录'我经历了什么'。",
            parameters={"content": "要记住的事件描述", "tags": "标签（逗号分隔）"},
            category="memory"
        )

    async def execute(self, context: Dict[str, Any], content: str, tags: str = "", **kwargs) -> Dict[str, Any]:
        user_id = context.get("user_id")
        agent_name = context.get("agent_name", "Alice")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        # Use add_memory with type="episodic"
        self.memory_store.add_memory(content, user_id, memory_type="episodic", tags=tag_list)
        return {
            "event": "memorize",
            "message": f"{agent_name} 将这段经历刻入了回忆...",
            "data": content
        }

class LearnSkill(Action):
    def __init__(self, registry):
        self.registry = registry
        super().__init__(
            name="learn_skill",
            description="习得行为。学习一个新的行为模式（通常是简单的动作）。",
            parameters={"skill_name": "技能名称", "skill_description": "技能描述"},
            category="learning"
        )

    async def execute(self, context: Dict[str, Any], skill_name: str, skill_description: str, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        from .learned import SimpleLearnedAction
        new_action = SimpleLearnedAction(skill_name, skill_description)
        self.registry.register(new_action)
        return {
            "event": "learn_skill",
            "message": f"{agent_name} 学会了新技能: {skill_name}!",
            "data": skill_name
        }

class ThinkAdd(Action):
    def __init__(self):
        super().__init__(
            name="think_add",
            description="开始一个新的思维链。当你发现一个新的独立问题需要长期跟踪思考时使用。",
            parameters={
                "topic": "思维链主题",
                "content": "当前思考内容"
            },
            category="cognition"
        )

    async def execute(self, context: Dict[str, Any], topic: str = "未命名思考", content: str = "...", **kwargs) -> Dict[str, Any]:
        persona = context.get("persona")
        agent_name = context.get("agent_name", "Alice")
        current_pool = []
        if persona:
            current_pool = persona.get_state()['intent'].get('thinking_pool', [])
            current_pool.append({
                "id": str(len(current_pool) + 1),
                "topic": topic,
                "content": [content], # Initialize as list
                "status": "active"
            })
            persona.update_state({"intent": {"thinking_pool": current_pool}})
            
        return {
            "event": "think_add",
            "message": f"{agent_name} 开启了新思考: {topic}",
            "data": {
                "topic": topic,
                "content": content,
                "thinking_pool": current_pool
            },
            "state_update": {
                "intent": {"thinking_pool": current_pool}
            }
        }

class ThinkUpdate(Action):
    def __init__(self):
        super().__init__(
            name="think_update",
            description="推进现有的思维链。当你在某个已有话题上有了新的进展或想法时使用。",
            parameters={
                "chain_id": "思维链ID",
                "content": "新的思考内容"
            },
            category="cognition"
        )

    async def execute(self, context: Dict[str, Any], chain_id: str, content: str = "...", **kwargs) -> Dict[str, Any]:
        persona = context.get("persona")
        agent_name = context.get("agent_name", "Alice")
        current_pool = []
        if persona:
            current_pool = persona.get_state()['intent'].get('thinking_pool', [])
            for item in current_pool:
                if item["id"] == chain_id:
                    # Extend the chain
                    if isinstance(item["content"], list):
                        item["content"].append(content)
                    else:
                        # Migration for old string format
                        item["content"] = [item["content"], content] if item["content"] else [content]
                        
            persona.update_state({"intent": {"thinking_pool": current_pool}})
            
        return {
            "event": "think_update",
            "message": f"{agent_name} 更新了思考 (ID: {chain_id})",
            "data": {
                "chain_id": chain_id,
                "content": content,
                "thinking_pool": current_pool
            },
            "state_update": {
                "intent": {"thinking_pool": current_pool}
            }
        }

class ThinkComplete(Action):
    def __init__(self, memory_store: WeaviateStore = None):
        self.memory_store = memory_store
        super().__init__(
            name="think_complete",
            description="完成一个思维链。当某个话题已经思考完毕或问题已解决时使用。",
            parameters={
                "chain_id": "思维链ID",
                "content": "最终结论或总结"
            },
            category="cognition"
        )

    async def execute(self, context: Dict[str, Any], chain_id: str, content: str = "已完成", **kwargs) -> Dict[str, Any]:
        persona = context.get("persona")
        agent_name = context.get("agent_name", "Alice")
        user_id = context.get("user_id")
        current_pool = []
        completed_item = None
        
        if persona:
            current_pool = persona.get_state()['intent'].get('thinking_pool', [])
            for item in current_pool:
                if item["id"] == chain_id:
                    item["status"] = "completed"
                    # Append conclusion
                    if isinstance(item["content"], list):
                        item["content"].append(f"【结论】{content}")
                    else:
                        # Migration
                        item["content"] = [item["content"], f"【结论】{content}"] if item["content"] else [f"【结论】{content}"]
                    completed_item = item
                        
            persona.update_state({"intent": {"thinking_pool": current_pool}})
        
        # Automatic Memorize on Completion
        memorize_msg = ""
        if completed_item and self.memory_store and user_id:
            # Construct memory content from the whole chain
            topic = completed_item.get("topic", "未命名思考")
            chain_content = "\n".join(completed_item.get("content", []))
            memory_text = f"【思考总结】主题：{topic}\n过程与结论：{chain_content}"
            
            self.memory_store.add_cognitive_memory(memory_text, user_id, tags=["thought_chain", "conclusion"])
            memorize_msg = " (已自动归档记忆)"

        return {
            "event": "think_complete",
            "message": f"{agent_name} 完成了思考 (ID: {chain_id}){memorize_msg}",
            "data": {
                "chain_id": chain_id,
                "content": content,
                "thinking_pool": current_pool
            },
            "state_update": {
                "intent": {"thinking_pool": current_pool}
            }
        }

class UpdateRelationship(Action):
    def __init__(self, memory_store: WeaviateStore):
        self.memory_store = memory_store
        super().__init__(
            name="update_relationship",
            description="更新社交关系状态。当你们的关系发生重要变化时使用。",
            parameters={
                "intimacy_change": "亲密度变化 (+/- 整数)",
                "trust_change": "信任度变化 (+/- 整数)",
                "new_stage": "新的关系阶段 (可选)",
                "summary": "当前关系状态的简短总结"
            },
            category="social"
        )

    async def execute(self, context: Dict[str, Any], intimacy_change: int = 0, trust_change: int = 0, new_stage: str = None, summary: str = None, **kwargs) -> Dict[str, Any]:
        user_id = context.get("user_id")
        agent_name = context.get("agent_name", "Alice")
        current_state = self.memory_store.get_social_state(user_id)
        
        new_intimacy = max(0, min(100, current_state.get("intimacy", 0) + int(intimacy_change)))
        new_trust = max(0, min(100, current_state.get("trust", 0) + int(trust_change)))
        stage = new_stage if new_stage else current_state.get("stage", "stranger")
        summary_text = summary if summary else current_state.get("summary", "")
        
        new_state = {
            "intimacy": new_intimacy,
            "trust": new_trust,
            "stage": stage,
            "summary": summary_text
        }
        
        self.memory_store.update_social_state(user_id, new_state)
        
        return {
            "event": "relationship_update",
            "message": f"{agent_name} 感觉你们的关系发生了变化 ({stage})...",
            "data": new_state,
            "state_update": {"social_state": new_state}
        }

class AddBelief(Action):
    def __init__(self, memory_store: WeaviateStore):
        self.memory_store = memory_store
        super().__init__(
            name="add_belief",
            description="增加信念。将学到的知识、观点或事实存入认知记忆(Cognitive)。用于记录'我知道了什么'。",
            parameters={
                "content": "信念内容",
                "tags": "标签（逗号分隔）"
            },
            category="memory"
        )

    async def execute(self, context: Dict[str, Any], content: str, tags: str = "", **kwargs) -> Dict[str, Any]:
        user_id = context.get("user_id")
        agent_name = context.get("agent_name", "Alice")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        self.memory_store.add_cognitive_memory(content, user_id, tags=tag_list)
        
        return {
            "event": "new_belief",
            "message": f"{agent_name} 形成了一个新的认知...",
            "data": content
        }

