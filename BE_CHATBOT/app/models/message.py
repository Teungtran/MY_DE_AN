from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True, description="Message ID")
    conversation_id: int = Field(foreign_key="conversation.id", description="Related conversation ID")
    type: Optional[str] = Field(default=None, description="Message type")
    content: Optional[str] = Field(default=None, description="Message content")
    category_code: Optional[int] = Field(default=None, description="Category code")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Last updated time")
    answer_id: Optional[int] = Field(default=None, description="Answer message ID")
