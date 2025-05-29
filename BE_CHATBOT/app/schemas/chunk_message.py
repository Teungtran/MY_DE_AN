from enum import Enum
from typing import Any, List, Optional, Dict, Union

from pydantic import BaseModel



# Define the Message model
class ChunkMessage(BaseModel):
    finishReason: Optional[str]
    content: Optional[str] = ""
    language: Optional[str] = ""
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_args: Optional[Dict[str, Any]] = None
    tool_call_type: Optional[str] = None
