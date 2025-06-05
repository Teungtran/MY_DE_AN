from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import END, StateGraph, START
from .state import AgenticState, Assistant,pop_dialog_state
from .tools.support_nodes import create_entry_node, create_tool_node_with_fallback
from .primary_assistant import assistant_runnable, update_tech_runnable, update_policy_runnable,route_policy_agent,route_primary_assistant,route_update_tech
from ..internal_graph.tech_agent import tech_sensitive_tools,tech_safe_tools
from ..research_graph.policy_agent import tools
from services.mongo_checkpoint import create_checkpointer
from utils.logging.logger import get_logger
from utils.token_counter import tiktoken_counter
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from.tools.support_nodes import format_message

logger = get_logger(__name__)

# Cache for graph state to avoid redundant calls
_graph_state_cache = {}

def get_cached_graph_state(graph, config, cache_key=None):
    """Get graph state with caching to avoid redundant calls."""
    if cache_key and cache_key in _graph_state_cache:
        return _graph_state_cache[cache_key]
    
    state = graph.get_state(config)
    if isinstance(state, tuple):
        state = state[0]
        
    if cache_key:
        _graph_state_cache[cache_key] = state
    
    return state

def clear_graph_state_cache():
    """Clear the graph state cache."""
    global _graph_state_cache
    _graph_state_cache.clear()

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

graph = setup_agentic_graph()

def format_message(message):
    """Format a message for display."""
    if hasattr(message, "content") and message.content:
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(message)

def test_fpt_shop_assistant(thread_id: str, user_message: str):
    """
    Send a message to the FPT Shop Assistant with a given thread_id,
    return only the final AI response and the final tool call.
    Handles both regular messages and tool call confirmations.
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    # Clear cache at start of new interaction
    clear_graph_state_cache()
    
    # Get initial state once and cache it
    initial_snapshot = get_cached_graph_state(graph, config, f"initial_{thread_id}")
    initial_chat_history = initial_snapshot.get("messages", []) if hasattr(initial_snapshot, 'get') else []
    initial_prompt_token = tiktoken_counter(initial_chat_history) if initial_chat_history else 0

    # Check for pending tool calls
    snapshot = get_cached_graph_state(graph, config, f"current_{thread_id}")
    if snapshot and snapshot.next:
        last_toolcall_message = None
        
        # Find last message with tool calls from the snapshot
        if hasattr(snapshot, 'values') and "messages" in snapshot.values:
            last_message = snapshot.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                last_toolcall_message = last_message
        
        if last_toolcall_message:
            # Handle user's response to tool call
            processed_set = set()
            all_messages = []
            all_tool_calls = []
            
            if user_message.strip().lower() == "y":
                result = graph.invoke(None, config)
            else:
                # User provided feedback/rejection
                tool_call_id = last_toolcall_message.tool_calls[0]["id"]
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call_id,
                                content=f"API call denied by user. Reasoning: '{user_message}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            
            # Process the result
            if "messages" in result:
                for msg in result["messages"]:
                    msg_content = format_message(msg)
                    msg_hash = hash(msg_content)
                    if msg_hash not in processed_set:
                        processed_set.add(msg_hash)
                        all_messages.append({
                            "content": msg_content,
                            "message": msg
                        })
                        
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                all_tool_calls.append({
                                    "name": tool_call['name'],
                                    "args": tool_call.get('args', {}),
                                    "id": tool_call['id'],
                                    "type": tool_call['type']
                                })
            
            # Get final response from processed messages
            final_response = ""
            for msg_data in reversed(all_messages):
                content = msg_data["content"]
                message = msg_data["message"]
                message_type = type(message).__name__
                
                if (message_type == "AIMessage" and 
                    content and 
                    content.strip() and 
                    not content.startswith("content=''") and
                    not content.startswith("The assistant is now")):
                    
                    final_response = content
                    break
            
            final_tool_call = all_tool_calls[-1] if all_tool_calls else None
            completion_token = tiktoken_counter([AIMessage(content=final_response)])
            
            # Get final state for token calculation  
            final_snapshot = get_cached_graph_state(graph, config, f"final_{thread_id}")
            chat_history = final_snapshot.get("messages", []) if hasattr(final_snapshot, 'get') else []
            prompt_token = tiktoken_counter(chat_history) if chat_history else 0
            
            return final_response, final_tool_call, prompt_token - initial_prompt_token, completion_token
    
    # Process new message
    processed_set = set()
    all_messages = []
    all_tool_calls = []
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "conversation_id": thread_id,  
        "dialog_state": ["primary_assistant"]
    }
    events = graph.stream(
        initial_state,
        config,
        stream_mode="values"
    )

    for event in events:
        if "messages" in event:
            for message in event["messages"]:
                msg_content = format_message(message)
                msg_hash = hash(msg_content)
                if msg_hash not in processed_set:
                    processed_set.add(msg_hash)
                    all_messages.append({
                        "content": msg_content,
                        "message": message
                    })
                    
                    # Collect all tool calls
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            all_tool_calls.append({
                                "name": tool_call['name'],
                                "args": tool_call.get('args', {}),
                                "id": tool_call['id'],
                                "type": tool_call['type']
                            })

    # Check if there's a pending tool call that needs approval
    post_snapshot = get_cached_graph_state(graph, config, f"post_{thread_id}")
    if post_snapshot and post_snapshot.next:
        if hasattr(post_snapshot, 'values') and "messages" in post_snapshot.values:
            last_message = post_snapshot.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_args = last_message.tool_calls[0]["args"]
                confirmation_message = (
                            f"Please confirm your request: {tool_args}, press 'y' to confirm or 'n' to reject.\n"
                            f"Vui lòng xác nhận yêu cầu: {tool_args}, nhấn 'y' để xác nhận hoặc 'n' để từ chối."
                        )
                return confirmation_message, None, 0, 0

    # Get final response
    final_response = ""
    for msg_data in reversed(all_messages):  # Start from the end
        content = msg_data["content"]
        message = msg_data["message"]
        message_type = type(message).__name__
        
        if (message_type == "AIMessage" and 
            content and 
            content.strip() and 
            not content.startswith("content=''") and
            not content.startswith("The assistant is now")):
            
            final_response = content
            break

    final_tool_call = all_tool_calls[-1] if all_tool_calls else None
    completion_token = tiktoken_counter([AIMessage(content=final_response)])

    # Get final state for token calculation
    final_snapshot = get_cached_graph_state(graph, config, f"final_{thread_id}")
    chat_history = final_snapshot.get("messages", []) if hasattr(final_snapshot, 'get') else []
    total_prompt_token = tiktoken_counter(chat_history) if chat_history else 0
    prompt_token = total_prompt_token - initial_prompt_token

    return final_response, final_tool_call, prompt_token, completion_token