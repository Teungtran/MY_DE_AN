from enum import Enum
from typing import Dict, Optional, Any, Union
import uuid

from pydantic import BaseModel, Field, EmailStr


class RoleEnum(Enum):
    USER = "HUMAN-MESSAGE"
    ASSISTANT = "AI-MESSAGE"
    CLIENT = "CLIENT"


class UserInputs(BaseModel):
    """
    Schema for the workflow input messages and configuration.
    """
    message: str = Field(..., description="Message sent from user.")
    conversation_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID of the user.")
class AuthenticatedUserInputs(BaseModel):
    """Internal model with user info after authentication"""
    conversation_id: str
    message: str
    user_id: str
    email: EmailStr
