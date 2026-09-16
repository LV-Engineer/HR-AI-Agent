import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.chat import ConversationSummary, MessageResponse
from app.services.conversation import ConversationService, ConversationNotFoundError

router = APIRouter(prefix='/conversations', tags=['conversations'])

@router.get('', response_model=list[ConversationSummary])
@limiter.limit('10/minute')
def list_conversations(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[ConversationSummary]:
    return ConversationService(db).list_conversation(uuid.UUID(user_id))

@router.get('/{conversation_id}/messages', response_model=list[MessageResponse])
@limiter.limit('10/minute')
def get_conversation_messages(
    request: Request,
    conversation_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    try:
        return ConversationService(db).get_messages(conversation_id, uuid.UUID(user_id))
    except ConversationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')