from typing import AsyncIterator
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.conversations.schemas import ConversationSummary, MessageResponse, QueryRequest
from app.conversations.service import ConversationService, ConversationNotFoundError

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

query_router = APIRouter(prefix='/query', tags=['query'])

@query_router.post('')
@limiter.limit('5/minute')
async def query(
    request: Request,
    payload: QueryRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    service = ConversationService(db)
    try:
        conversation_id = service.resolve_conversation(payload.conversation_id, uuid.UUID(user_id), payload.question)
    except ConversationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')

    async def event_stream() -> AsyncIterator[str]:
        async for event in service.ask_and_persist(conversation_id, payload.question):
            yield f'data: {json.dumps({**event, 'conversation_id': str(conversation_id)})}\n\n'

    return StreamingResponse(event_stream(), media_type='text/event-stream')
