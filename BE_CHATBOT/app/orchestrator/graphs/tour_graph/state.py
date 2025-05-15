from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class TourAgentState(TypedDict):
    """State of the retrieval graph / agent."""
    messages: Annotated[list[AnyMessage], add_messages]
    prompt_token: int
    completion_token: int