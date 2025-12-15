from typing import Annotated, Optional, List
from langchain_core.messages import AnyMessage, AIMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict, Literal
from langchain_core.runnables import Runnable
from langchain_core.messages import ToolMessage
from pydantic import EmailStr
from app.utils.logging.logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)

def merge_recommended_devices(left: Optional[List[str]], right: Optional[List[str]]) -> Optional[List[str]]:
    """Merge recommended devices lists, with right taking precedence."""
    if right is None:
        return left
    return right


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

def get_limited_conversation_pairs(state, num_pairs: int = 3) -> list:
    """Get the latest N conversation pairs (HumanMessage + AIMessage)."""
    all_messages = state.get("messages", [])
    
    if not all_messages:
        return all_messages
    
    # Group messages into conversation turns
    pairs = []
    i = 0
    while i < len(all_messages):
        if isinstance(all_messages[i], HumanMessage):
            pair = [all_messages[i]]
            j = i + 1
            while j < len(all_messages) and isinstance(all_messages[j], AIMessage):
                pair.append(all_messages[j])
                j += 1
            pairs.append(pair)
            i = j
        else:
            i += 1
    
    # Get latest N pairs and flatten
    latest_pairs = pairs[-num_pairs:] if len(pairs) > num_pairs else pairs
    limited_messages = [msg for pair in latest_pairs for msg in pair]
    
    return limited_messages

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
        
        # Get limited messages
        limited_messages = get_limited_conversation_pairs(state, num_pairs=3)
        state_with_limited_messages = {**state, "messages": limited_messages}
        
        while True:
            result = self.runnable.invoke(state_with_limited_messages)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                # Use limited messages for retry, not original state
                messages = state_with_limited_messages["messages"] + [("user", "Respond with a real output.")]
                state_with_limited_messages = {**state_with_limited_messages, "messages": messages}
            else:
                break
                
        if hasattr(result, "tool_calls") and result.tool_calls:
            for tool_call in result.tool_calls:
                if tool_call.get("name") == "recommend_system" and tool_call.get("return_value"):
                    return_value = tool_call.get("return_value")
                    if isinstance(return_value, tuple) and len(return_value) > 1:
                        response, device_names = return_value
                        global recommended_devices_cache
                        recommended_devices_cache = device_names
                        if isinstance(state, dict):
                            state["recommended_devices"] = device_names
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