from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any, Dict

class AgentState(TypedDict):
    input: str
    user_id: str
    user_profile: Dict[str, Any]
    agent_name: str
    persona_prompt: str
    history_str: str
    perception_queue_str: str
    memories: List[Dict[str, Any]]
    thought_data: Dict[str, Any]
    output: str

def create_graph(agent_instance):
    """
    Creates the LangGraph for the agent.
    """
    graph = StateGraph(AgentState)

    # Define nodes
    # We wrap the async methods to match LangGraph signature if needed, 
    # but here we assume the agent_instance methods handle the signature.
    
    graph.add_node("observe", agent_instance.run_observe)
    graph.add_node("think", agent_instance.run_think)
    graph.add_node("act", agent_instance.run_act)
    
    graph.add_edge("observe", "think")
    graph.add_edge("think", "act")
    graph.add_edge("act", END)

    graph.set_entry_point("observe")

    return graph.compile()
