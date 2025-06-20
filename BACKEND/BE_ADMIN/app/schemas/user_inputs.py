from enum import Enum
from typing import Dict, Optional, Any, Union

from pydantic import BaseModel, Field


class RoleEnum(Enum):
    USER = "HUMAN-MESSAGE"
    ASSISTANT = "AI-MESSAGE"
    CLIENT = "CLIENT"


class UserInputs(BaseModel):
    """
    Schema for the workflow input messages and configuration.
    """
    user_id: str = Field(..., description="User ID.")
    message: str = Field(..., description="Message sent from user.")
    conversation_id: str = Field(..., description="Session ID of the user.")

    
