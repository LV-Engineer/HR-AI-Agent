from typing import AsyncIterator
import json
import uuid

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.query import QueryRequest
from app.services.conversation import ConversationService, ConversationNotFoundError

router = APIRouter(prefix='/query', tags=['query'])

@router.post('')
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