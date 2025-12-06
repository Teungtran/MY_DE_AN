from typing import Annotated, Optional, List
from langchain_core.messages import AnyMessage, AIMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict, Literal
from langchain_core.runnables import Runnable
from langchain_core.messages import ToolMessage
from pydantic import EmailStr
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

def merge_recommended_devices(left: Optional[List[str]], right: Optional[List[str]]) -> Optional[List[str]]:
    """Merge recommended devices lists, with right taking precedence."""
    if right is None:
        return left
    return right


def get_safe_recent_messages(messages: List[AnyMessage], limit: int = 5) -> List[AnyMessage]:
    """
    Get the last N messages, but if the first message is a ToolMessage,
    extend backwards to include its parent AIMessage with tool_calls.
    
    This prevents OpenAI API error: "messages with role 'tool' must be 
    a response to a preceeding message with 'tool_calls'."
    """
    if not messages or len(messages) <= limit:
        return messages
    
    # Start with last N messages
    recent = messages[-limit:]
    
    if isinstance(recent[0], ToolMessage):

        for i in range(len(messages) - limit - 1, -1, -1):
            msg = messages[i]
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                recent = messages[i:]
                logger.info(f"Extended context to include tool call: {len(messages)} -> {len(recent)} messages")
                break
        else:
            logger.warning(f"Could not find parent AIMessage for ToolMessage, using {len(recent)} messages")
    
    return recent


class InputState(TypedDict):
    """Represents the input state for the agent.

    This class defines the structure of the input state, which includes
    the messages exchanged between the user and the agent. It serves as
    a restricted version of the full State, providing a narrower interface
    to the outside world compared to what is maintained internally.
    """

    messages: Annotated[list[AnyMessage], add_messages]


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state.
    
    Args:
        left: The current dialog stack
        right: The operation to perform ('pop' or a new state to push)
        
    Returns:
        The updated dialog stack
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class AgenticState(InputState):
    """State of the retrieval graph / agent."""

    dialog_state: Annotated[
        list[Literal["primary_assistant", "call_shop_agent", "call_it_agent","call_appointment_agent"]],
        update_dialog_stack,
    ]
    recommended_devices: Annotated[List[str], merge_recommended_devices]
    conversation_id: Annotated[str, "The unique identifier for the conversation"]
    user_id: Annotated[str, "The unique identifier for the user"]
    email: Annotated[EmailStr,"The email of the customer ordering"]
class Assistant:
    def __init__(self, runnable: Runnable, agent_name: str = "Unknown Agent"):
        self.runnable = runnable
        self.agent_name = agent_name

    def __call__(self, state: AgenticState):
        conversation_id = state.get("conversation_id", "N/A")
        user_id = state.get("user_id", "N/A")
        dialog_state = state.get("dialog_state", [])
        
        logger.info(
            f"[AGENT PROCESSING] Agent: {self.agent_name} | "
            f"Conversation ID: {conversation_id} | "
            f"User ID: {user_id} | "
            f"Dialog state: {dialog_state}"
        )
        
        while True:
            # Get recent messages safely (handles tool call chains)
            recent_messages = get_safe_recent_messages(state["messages"], limit=5)
            limited_state = {**state, "messages": recent_messages}
            logger.info(
                f"[AGENT PROCESSING] {self.agent_name} processing with {len(recent_messages)}/{len(state['messages'])} messages"
            )
            result = self.runnable.invoke(limited_state)

            # Log tool calls if any
            if hasattr(result, "tool_calls") and result.tool_calls:
                tool_names = [tc.get("name", "unknown") for tc in result.tool_calls]
                logger.info(
                    f"[AGENT PROCESSING] {self.agent_name} generated tool calls: {tool_names} | "
                    f"Conversation ID: {conversation_id}"
                )

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                logger.warning(
                    f"[AGENT PROCESSING] {self.agent_name} generated empty response, retrying | "
                    f"Conversation ID: {conversation_id}"
                )
                messages = get_safe_recent_messages(state["messages"], limit=5) + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        
        logger.info(
            f"[AGENT PROCESSING] {self.agent_name} completed processing | "
            f"Conversation ID: {conversation_id}"
        )
        return {"messages": result}
    
    
def pop_dialog_state(state: AgenticState) -> dict:
    """Pop the dialog stack and return to the main assistant."""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }