from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel

# Define Pydantic models


# Define the Enum for the 'type' field
class MessageType(str, Enum):
    message_chunk = "message_chunk"
    tool_call = "tool_call"
    artifact = "artifact"


class NameType(str, Enum):
    agent = "agent"
    tool_call = "tool_call"


# Define the Artifact model
class Artifact(BaseModel):
    sources: List[str] = []
    form: dict[str, Any] = {}
    data: List[dict[str, Any]] = []


# Define the Message model
class ChunkMessage(BaseModel):
    name: str
    type: Any  # Use the MessageType enum here # TODO:  old have type: MessageType
    id: str
    finishReason: Optional[str]
    content: Optional[str] = ""
    language: Optional[str] = ""
    artifact: Optional[Artifact] = None  # Default to None for optional field
