from langgraph.graph import END, StateGraph, START
from .state import AgenticState, Assistant,pop_dialog_state
from .tools.support_nodes import create_entry_node, create_tool_node_with_fallback
from .primary_assistant import assistant_runnable, update_it_runnable, update_shop_runnable,update_appointment_runnable, route_update_shop,route_primary_assistant,route_update_it,route_update_appointment
from ..shop_graph.shop_agent import shop_sensitive_tools,shop_safe_tools
from ..it_graph.it_agent import it_sensitive_tools,it_safe_tools
from ..appointment_graph.appointment_agent import appointment_sensitive_tools,appointment_safe_tools
from ..rag_tool.tools.policy_tool import RAG_Agent
from ..web_crawler.tool import url_extraction, url_followup

from services.mongo_checkpoint import create_checkpointer
from utils.logging.logger import get_logger

logger = get_logger(__name__)

def setup_agentic_graph():
    """Create the main agent graph with all nodes and edges."""
    builder = StateGraph(AgenticState)
    
    # Add nodes
    builder.add_node("primary_assistant", Assistant(assistant_runnable))

    # shop assistant nodes
    builder.add_node("enter_shop_node", create_entry_node("Shop Assistant", "call_shop_agent"))
    builder.add_node("call_shop_agent", Assistant(update_shop_runnable))
    builder.add_node("update_shop_sensitive_tools", create_tool_node_with_fallback(shop_sensitive_tools))
    builder.add_node("update_shop_safe_tools", create_tool_node_with_fallback(shop_safe_tools))
    builder.add_node("leave_skill", pop_dialog_state)
    
    # it assistant nodes
    builder.add_node("enter_it_node", create_entry_node("IT Assistant", "call_it_agent"))
    builder.add_node("call_it_agent", Assistant(update_it_runnable))
    builder.add_node("update_it_sensitive_tools", create_tool_node_with_fallback(it_sensitive_tools))
    builder.add_node("update_it_safe_tools", create_tool_node_with_fallback(it_safe_tools))
    
    # appointment assistant nodes
    builder.add_node("enter_appointment_node", create_entry_node("Appointment Assistant", "call_appointment_agent"))
    builder.add_node("call_appointment_agent", Assistant(update_appointment_runnable))
    builder.add_node("update_appointment_sensitive_tools", create_tool_node_with_fallback(appointment_sensitive_tools))
    builder.add_node("update_appointment_safe_tools", create_tool_node_with_fallback(appointment_safe_tools))
    
    # RAG agent node
    builder.add_node("rag_agent_node", create_tool_node_with_fallback([RAG_Agent]))
    # URL handle nodes
    builder.add_node("url_agent_node", create_tool_node_with_fallback([url_extraction]))
    builder.add_node("url_followup_node", create_tool_node_with_fallback([url_followup]))
    
    # Add edges
    builder.add_edge(START, "primary_assistant")
    
    # shop assistant edges
    builder.add_edge("enter_shop_node", "call_shop_agent")
    builder.add_edge("update_shop_sensitive_tools", "call_shop_agent")
    builder.add_edge("update_shop_safe_tools", "call_shop_agent")
    builder.add_edge("leave_skill", "primary_assistant")
    
    # it assistant edges
    builder.add_edge("enter_it_node", "call_it_agent")
    builder.add_edge("update_it_sensitive_tools", "call_it_agent")
    builder.add_edge("update_it_safe_tools", "call_it_agent")
    
    # appointment assistant edges
    builder.add_edge("enter_appointment_node", "call_appointment_agent")
    builder.add_edge("update_appointment_sensitive_tools", "call_appointment_agent")
    builder.add_edge("update_appointment_safe_tools", "call_appointment_agent")
    
    builder.add_edge("rag_agent_node", "primary_assistant")
    builder.add_edge("url_agent_node", "primary_assistant")
    builder.add_edge("url_followup_node", "primary_assistant")

    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        ["enter_shop_node", "enter_it_node", "enter_appointment_node", "rag_agent_node", "url_agent_node", "url_followup_node", END],
    )

    builder.add_conditional_edges(
        "call_shop_agent",
        route_update_shop,
        ["update_shop_sensitive_tools", "update_shop_safe_tools", "leave_skill", END],
    )
    
    builder.add_conditional_edges(
        "call_it_agent",
        route_update_it,
        ["update_it_sensitive_tools", "update_it_safe_tools", "leave_skill", END],
    )
    
    builder.add_conditional_edges(
        "call_appointment_agent",
        route_update_appointment,
        ["update_appointment_sensitive_tools", "update_appointment_safe_tools", "leave_skill", END],
    )

    logger.info("Attempting to connect to MongoDB...")

    checkpointer = create_checkpointer()

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["update_shop_sensitive_tools", "update_it_sensitive_tools", "update_appointment_sensitive_tools"],
    )
    return graph

