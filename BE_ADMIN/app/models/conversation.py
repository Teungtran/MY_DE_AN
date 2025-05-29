from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Column, Field, SQLModel


class Conversation(SQLModel, table=True):  # type: ignore
    id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, index=True))
    user_id: Optional[int] = Field(default=None, index=True, description="User ID")
    guest_id: Optional[str] = Field(default=None, description="Guest ID")
    status: Optional[str] = Field(default=None, description="Conversation status")
    title: str = Field(default="New chat", description="Conversation title")
    language: Optional[str] = Field(default=None, description="Conversation language")
    total_token: Optional[int] = Field(default=None, description="Total tokens in the conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last updated time")

    class Config:
        arbitrary_types_allowed = True
