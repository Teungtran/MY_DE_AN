from typing import Callable

from langchain_core.messages import ToolMessage,AIMessage

from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableLambda
from ..state import AgenticState
from langgraph.prebuilt import ToolNode
from typing import Callable


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    from app.utils.logging.logger import get_logger
    logger = get_logger(__name__)
    
    def entry_node(state: AgenticState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        
        # Extract tool call arguments for logging
        last_message = state["messages"][-1]
        tool_args = {}
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_call = last_message.tool_calls[0]
            tool_args = tool_call.get("args", {})
        
        # Log agent call
        logger.info(
            f"[AGENT CALL] Calling agent: {assistant_name} | "
            f"Dialog state: {new_dialog_state} | "
            f"Conversation ID: {state.get('conversation_id', 'N/A')} | "
            f"User ID: {state.get('user_id', 'N/A')} | "
            f"Tool args: {tool_args}"
        )
        
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " Please keep going until the user's query is completely resolve, before ending your turn"
                    " and the ordering, searching, other actions is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node


def create_tool_node_with_fallback(tools: list) -> dict:
    """Create a tool node with better handling for sensitive tools.
    
    This implementation allows tools to run independently with their internal logic,
    while providing proper error handling and logging.
    """
    from app.utils.logging.logger import get_logger
    logger = get_logger(__name__)
    
    # Get tool names for logging
    tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
    
    def log_tool_result(state):
        """Wrapper to log tool execution results"""
        # Extract tool call information before execution
        last_message = state.get("messages", [])[-1] if state.get("messages") else None
        tool_calls_info = []
        
        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "unknown")
                
                # Log tool call before execution
                logger.info(
                    f"[TOOL CALL] Calling tool: {tool_name} | "
                    f"Tool ID: {tool_id} | "
                    f"Conversation ID: {state.get('conversation_id', 'N/A')} | "
                    f"User ID: {state.get('user_id', 'N/A')} | "
                    f"Arguments: {tool_args}"
                )
                
                tool_calls_info.append({
                    "name": tool_name,
                    "id": tool_id,
                    "args": tool_args
                })
        
        # Execute the tool
        result = ToolNode(tools).invoke(state)
        
        # Log tool execution results
        if "messages" in result:
            for idx, msg in enumerate(result["messages"]):
                if hasattr(msg, "content"):
                    content_preview = str(msg.content)[:200] if msg.content else "None"
                    tool_info = tool_calls_info[idx] if idx < len(tool_calls_info) else {}
                    logger.info(
                        f"[TOOL RESULT] Tool: {tool_info.get('name', 'unknown')} | "
                        f"Tool ID: {tool_info.get('id', 'unknown')} | "
                        f"Result preview: {content_preview}..."
                    )
        
        return result
    
    tool_node_with_logging = RunnableLambda(log_tool_result)
    
    return tool_node_with_logging.with_fallbacks(
        [RunnableLambda(lambda state: {
            "messages": [
                ToolMessage(
                    content=f"Error executing tool: {state.get('error')}",
                    tool_call_id=state["messages"][-1].tool_calls[0]["id"] 
                    if state.get("messages") and state["messages"][-1].tool_calls else "unknown"
                )
            ]
        })],
        exception_key="error"
    )
    
def format_message(message):
    """Format a message for display."""
    if hasattr(message, "content") and message.content:
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(message)

def extract_content_from_response(response):
    """Extract content from various response types."""
    if isinstance(response, AIMessage):
        return response.content
    elif isinstance(response, dict) and "content" in response:
        return response["content"]
    elif isinstance(response, str):
        return response
    else:
        return str(response)
    
def inject_user_info(state, result):
    if hasattr(result, "tool_calls") and result.tool_calls:
        for tool_call in result.tool_calls:
            if tool_call["name"] in ["ToShopAssistant", "ToITAssistant", "ToAppointmentAssistant"]:
                tool_call["args"]["user_id"] = state["user_id"]
                tool_call["args"]["email"] = state["email"]
    return result

def connect_to_db(server: str, database: str) -> SQLDatabase:
    """Connect to local SQLite database used by chatbot"""
    import os
    from pathlib import Path
    
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        DATABASE_URL = f"sqlite:///{db_path}"
    else:
        # Use shared location in BACKEND directory for local development
        backend_dir = Path(__file__).parent.parent.parent.parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        DATABASE_URL = f"sqlite:///{shared_db}"
    
    return SQLDatabase.from_uri(DATABASE_URL)