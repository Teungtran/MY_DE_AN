from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import select

from controllers.deps import SessionDep
from models.conversation import Conversation

router = APIRouter()


@router.get("/list-conversation")
def list_conversations(
    session: SessionDep,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit for pagination"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'completed')"),
):
    """
    Get the list of conversations with pagination (offset + limit).
    You can provide status to filter.
    """

    statement = select(Conversation)
    if status:
        statement = statement.where(Conversation.status == status)
    statement = statement.order_by(Conversation.created_at.desc()).offset(offset).limit(limit)  # type: ignore

    results = session.exec(statement).all()
    return [
        {
            "id": str(conv.id),
            "user_id": str(conv.user_id),
            "status": conv.status,
            "language": conv.language,
            "total_token": str(conv.total_token),
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        }
        for conv in results
    ]
