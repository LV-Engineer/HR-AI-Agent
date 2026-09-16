import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ConversationSummary, MessageResponse

router = APIRouter(prefix='/conversations', tags=['conversations'])

@router.get('', response_model=list[ConversationSummary])
@limiter.limit('10/minute')
def list_conversations(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[Conversation]:
    return list(db.scalars(
        select(Conversation)
        .where(Conversation.user_id == uuid.UUID(user_id))
        .order_by(Conversation.created_at.desc())
    ))

@router.get('/{conversation_id}/messages', response_model=list[MessageResponse])
@limiter.limit('10/minute')
def get_conversation_messages(
    request: Request,
    conversation_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Message]:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == uuid.UUID(user_id),
        )
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')

    return list(db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ))