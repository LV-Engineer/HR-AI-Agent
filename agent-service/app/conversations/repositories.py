import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conversations.models import Conversation, Message

class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        return list(self._db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        ))

    def get_for_user(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        return self._db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    def create(self, user_id: uuid.UUID, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._db.add(conversation)
        self._db.flush()
        return conversation

    def delete(self, conversation: Conversation) -> None:
        self._db.delete(conversation)

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
