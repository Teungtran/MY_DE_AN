from typing import Callable

from langchain_core.messages import ToolMessage,AIMessage

from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableLambda
from ..state import AgenticState
from langgraph.prebuilt import ToolNode
def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: AgenticState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " Please keep going until the user's query is completely resolve, before ending your turn"
                    " and the booking, searching, other actions is not complete until after you have successfully invoked the appropriate tool."
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
    tool_node = ToolNode(tools)
    
    return tool_node.with_fallbacks(
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
    
def inject_user_id(state, result):
    if hasattr(result, "tool_calls") and result.tool_calls:
        for tool_call in result.tool_calls:
            if tool_call["name"] in ["ToShopAssistant", "ToITAssistant", "ToAppointmentAssistant"]:
                tool_call["args"]["user_id"] = state["user_id"]
    return result

def connect_to_db(server: str, database: str) -> SQLDatabase:
    """Connect to SQL Server database"""
    db_uri = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return SQLDatabase.from_uri(db_uri)