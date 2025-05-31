
from langgraph.graph import END, StateGraph, START
from .state import AgenticState, Assistant,pop_dialog_state
from .tools.support_nodes import create_entry_node, create_tool_node_with_fallback
from .primary_assistant import assistant_runnable, update_tech_runnable, update_policy_runnable,route_policy_agent,route_primary_assistant,route_update_tech
from ..tech_graph.tech_agent import tech_sensitive_tools,tech_safe_tools
from ..rag_graph.policy_agent import tools
from services.mongo_checkpoint import create_checkpointer
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def setup_agentic_graph():
    """Create the main agent graph with all nodes and edges."""
    builder = StateGraph(AgenticState)
    
    # Add nodes
    builder.add_node("primary_assistant", Assistant(assistant_runnable))
    
    # Tech assistant nodes
    builder.add_node("enter_tech_node", create_entry_node("Tech Assistant", "call_tech_agent"))
    builder.add_node("call_tech_agent", Assistant(update_tech_runnable))
    builder.add_node("update_tech_sensitive_tools", create_tool_node_with_fallback(tech_sensitive_tools))
    builder.add_node("update_tech_safe_tools", create_tool_node_with_fallback(tech_safe_tools))
    builder.add_node("leave_skill", pop_dialog_state)
    
    # Policy assistant nodes
    builder.add_node("enter_policy_node", create_entry_node("Policy Assistant", "call_policy_agent"))
    builder.add_node("call_policy_agent", Assistant(update_policy_runnable))
    builder.add_node("policy_tool", create_tool_node_with_fallback(tools))

    # Add edges
    builder.add_edge(START, "primary_assistant")
    
    # Tech assistant edges
    builder.add_edge("enter_tech_node", "call_tech_agent")
    builder.add_edge("update_tech_sensitive_tools", "call_tech_agent")
    builder.add_edge("update_tech_safe_tools", "call_tech_agent")
    builder.add_edge("leave_skill", "primary_assistant")
    
    # Policy assistant edges
    builder.add_edge("enter_policy_node", "call_policy_agent")
    builder.add_edge("policy_tool", "call_policy_agent")
    
    # Add conditional edges
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        ["enter_tech_node", "enter_policy_node", END],
    )
    
    builder.add_conditional_edges(
        "call_tech_agent",
        route_update_tech,
        ["update_tech_sensitive_tools", "update_tech_safe_tools", "leave_skill", END],
    )
    
    builder.add_conditional_edges(
        "call_policy_agent",
        route_policy_agent,
        ["policy_tool", "leave_skill", END],
    )
    

    logger.info("Attempting to connect to MongoDB...")

    checkpointer = create_checkpointer()

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["update_tech_sensitive_tools"],
    )
    return graph

