from pydantic import BaseModel


class ConversationResponse(BaseModel):
    """
    Response model for a newly created conversation.

    Attributes:
        conversationId: Unique identifier for the conversation (Snowflake ID).
        createdAt: ISO 8601 timestamp of creation in UTC+7.
    """

    conversation_id: str
    created_at: str
