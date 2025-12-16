from typing import Annotated, Optional, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, ToolMessage, trim_messages
from langgraph.graph import add_messages
from typing_extensions import TypedDict, Literal
from langchain_core.runnables import Runnable
from pydantic import EmailStr
from app.utils.logging.logger import get_logger

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
    def __init__(self, runnable: Runnable, agent_name: str = "Unknown Agent", max_tokens: int = 100000):
        self.runnable = runnable
        self.agent_name = agent_name
        self.max_tokens = max_tokens

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
        

        messages = state.get("messages", [])
        if messages and len(messages) > 10:  # Only trim if there are many messages
            try:
                trimmed_messages = trim_messages(
                    messages,
                    max_tokens=self.max_tokens,
                    strategy="last",
                    token_counter=self.runnable, 
                    start_on="human",
                    include_system=True,
                    allow_partial=False,
                )
                state = {**state, "messages": trimmed_messages}
                logger.debug(
                    f"Trimmed messages from {len(messages)} to {len(trimmed_messages)} "
                    f"(max_tokens: {self.max_tokens})"
                )
            except Exception as e:
                logger.warning(f"Failed to trim messages: {e}. Using all messages.")
        
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
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