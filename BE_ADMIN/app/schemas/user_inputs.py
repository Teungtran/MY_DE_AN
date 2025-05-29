from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class RoleEnum(Enum):
    USER = "HUMAN-MESSAGE"
    ASSISTANT = "AI-MESSAGE"
    CLIENT = "CLIENT"


class UserInputs(BaseModel):
    """
    Schema for the workflow input messages and configuration.
    """

    # user_id: Optional[str] = Field("xxx1308", description="ID of a user.") # TODO: user_input passed through header
    # role: RoleEnum = Field(RoleEnum.USER, description="Role of the sender of the message.") # TODO: role passed throught headers
    message: str = Field(..., description="Message sent from user.")
    args: Optional[Dict] = Field({}, description="Args sent from client to validate tool args.")
    conversation_id: str = Field(..., description="Session ID of the user.")
    category_code: Optional[dict] = Field(None, description="Category code of the user.")
