from typing import AsyncIterator
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.agent import ask_agent
from app.core.rate_limit import limiter
from app.core.db import get_db, SessionLocal
from app.core.deps import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.query import QueryRequest

router = APIRouter(prefix='/query', tags=['query'])

TITLE_MAX_LENGTH = 60

@router.post('')
@limiter.limit('5/minute')
async def query(
    request: Request,
    payload: QueryRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    if payload.conversation_id is not None:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == uuid.UUID(user_id)
            )
        )
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')
    else:
        conversation = Conversation(user_id=uuid.UUID(user_id), title=payload.question[:TITLE_MAX_LENGTH])
        db.add(conversation)
        db.flush()

    history = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = [{'role': m.role, 'content': m.content} for m in history]
    messages.append({'role': 'user', 'content': payload.question})
    conversation_id = conversation.id    
    db.commit()

    async def event_stream() -> AsyncIterator[str]:
        final_answer = ''
        async for event in ask_agent(messages):
            if event['type'] == 'answer':
                final_answer = event['content']
            yield f'data: {json.dumps({**event, 'conversation_id': str(conversation_id)})}\n\n'

        with SessionLocal() as write_db:
            write_db.add(Message(conversation_id=conversation_id, role='user', content=payload.question, created_at=datetime.now(timezone.utc)))
            write_db.add(Message(conversation_id=conversation_id, role='assistant', content=final_answer, created_at=datetime.now(timezone.utc)))
            write_db.commit()

    return StreamingResponse(event_stream(), media_type='text/event-stream')