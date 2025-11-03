from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict

from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import ToolMessage

class InputState(TypedDict):
    """Represents the input state for the agent.

    This class defines the structure of the input state, which includes
    the messages exchanged between the user and the agent. It serves as
    a restricted version of the full State, providing a narrower interface
    to the outside world compared to what is maintained internally.
    """

    messages: Annotated[list[AnyMessage], add_messages]


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