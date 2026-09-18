import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from sqlalchemy.orm import Session

from app.core.agent import ask_agent
from app.core.db import SessionLocal
from app.conversations.repositories import ConversationRepository, MessageRepository
from app.conversations.schemas import ConversationSummary, MessageResponse

TITLE_MAX_LENGTH = 60
FALLBACK_ANSWER = 'Не вдалося отримати відповідь від асистента.'

class ConversationNotFoundError(Exception):
    pass

class ConversationService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._conversations = ConversationRepository(db)
        self._messages = MessageRepository(db)

    def list_conversation(self, user_id: uuid.UUID) -> list[ConversationSummary]:
        conversations = self._conversations.list_for_user(user_id)
        return [ConversationSummary.model_validate(c) for c in conversations]

    def get_messages(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> list[MessageResponse]:
        conversation = self._conversations.get_for_user(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError()
        messages = self._messages.list_for_conversation(conversation_id)
        return [MessageResponse.model_validate(m) for m in messages]

    def resolve_conversation(self, conversation_id: uuid.UUID | None, user_id: uuid.UUID, question: str) -> uuid.UUID:
        if conversation_id is not None:
            conversation = self._conversations.get_for_user(conversation_id, user_id)
            if conversation is None:
                raise ConversationNotFoundError()
            return conversation.id

        conversation = self._conversations.create(user_id, question[:TITLE_MAX_LENGTH])
        self._db.commit()
        return conversation.id

    def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        conversation = self._conversations.get_for_user(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError()
        self._conversations.delete(conversation)
        self._db.commit()

    def build_history(self, conversation_id: uuid.UUID) -> list[dict[str, str]]:
        messages = self._messages.list_for_conversation(conversation_id)
        return [{'role': m.role, 'content': m.content} for m in messages]

    async def ask(self, conversation_id: uuid.UUID, question: str) -> AsyncIterator[dict[str, Any]]:
        self.persist_user_message(conversation_id, question)
        messages = self.build_history(conversation_id)
        async for event in ask_agent(messages):
            yield event

    async def ask_and_persist(self, conversation_id: uuid.UUID, question: str) -> AsyncIterator[dict[str, Any]]:
        final_answer = ''
        async for event in self.ask(conversation_id, question):
            if event['type'] == 'answer':
                final_answer = event['content']
            yield event
        self.persist_assistant_message(conversation_id, final_answer or FALLBACK_ANSWER)

    @staticmethod
    def persist_user_message(conversation_id: uuid.UUID, question: str) -> None:
        with SessionLocal() as db:
            MessageRepository(db).create(conversation_id, 'user', question, datetime.now(timezone.utc))
            db.commit()

    @staticmethod
    def persist_assistant_message(conversation_id: uuid.UUID, answer: str) -> None:
        with SessionLocal() as db:
            MessageRepository(db).create(conversation_id, 'assistant', answer, datetime.now(timezone.utc))
            db.commit()
