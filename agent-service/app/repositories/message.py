import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message

class MessageRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        return list(self._db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        ))

    def create(self, conversation_id: uuid.UUID, role: str, content: str, created_at: datetime) -> None:
        self._db.add(Message(conversation_id=conversation_id, role=role, content=content, created_at=created_at))