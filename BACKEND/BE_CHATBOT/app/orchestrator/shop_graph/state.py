from pydantic import BaseModel, Field, EmailStr
from typing_extensions import Optional
class ToShopAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle electronics products recommendations, orders and cancellations, with user_id"""
    user_id: str = Field(
        description="The id of user from 'AgenticState'"
    ),
    email: EmailStr = Field(
        description="The email of user from 'AgenticState'"
    ),
    request: str = Field(
        description="Any necessary followup questions the Shop assistant should clarify before proceeding."
    )