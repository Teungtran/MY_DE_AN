from enum import Enum
from typing import Any, List, Optional, Dict, Union

from pydantic import BaseModel



# Define the Message model
class ChunkMessage(BaseModel):
    response: Optional[str] = ""
    tools: Optional[List[Dict[str, Any]]] = None
    prompt_token: Optional[int] = None
    completion_token: Optional[int] = None
