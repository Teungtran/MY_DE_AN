from pydantic import BaseModel, Field,EmailStr
from typing_extensions import Optional

class ToITAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle FPT IT-related questions, with user_id"""
    user_id: str = Field(
        description="The id of user from 'AgenticState'"
    ),
    email: EmailStr = Field(
        description="The email of user from 'AgenticState'"
    ),
    request: str = Field(
        description="Any necessary followup questions the IT assistant should clarify before proceeding."
    )
