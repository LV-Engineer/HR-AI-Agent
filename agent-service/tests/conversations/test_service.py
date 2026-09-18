import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.conversations.models import Conversation, Message
from app.conversations import service as conversation_service_module
from app.conversations.service import ConversationNotFoundError, ConversationService


def _user_id(db_session: Session, email: str) -> uuid.UUID:
    return db_session.execute(
        text('SELECT id FROM auth.users WHERE email = :email'), {'email': email}
    ).scalar_one()

class TestListConversation:
    def test_returns_only_own_conversations_newest_first(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        other_user_id = db_session.execute(
            text("SELECT auth.create_user(:email, :password)"),
            {'email': 'other.conv@hirelume.com', 'password': 'password123'},
        ).scalar_one()

        now = datetime.now(timezone.utc)
        db_session.add(Conversation(user_id=user_id, title='Older', created_at=now - timedelta(minutes=5)))
        db_session.add(Conversation(user_id=user_id, title='Newer', created_at=now))
        db_session.add(Conversation(user_id=other_user_id, title='Not mine', created_at=now))
        db_session.commit()

        result = ConversationService(db_session).list_conversation(user_id)

        assert [c.title for c in result] == ['Newer', 'Older']

class TestGetMessages:
    def test_returns_messages_for_own_conversation(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        conversation = Conversation(user_id=user_id, title='Test')
        db_session.add(conversation)
        db_session.flush()
        db_session.add(Message(conversation_id=conversation.id, role='user', content='Hi', created_at=datetime.now(timezone.utc)))
        db_session.add(Message(conversation_id=conversation.id, role='assistant', content='Hello', created_at=datetime.now(timezone.utc)))
        db_session.commit()

        result = ConversationService(db_session).get_messages(conversation.id, user_id)

        assert [(m.role, m.content) for m in result] == [('user', 'Hi'), ('assistant', 'Hello')]

    def test_raises_for_unknown_conversation(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        with pytest.raises(ConversationNotFoundError):
            ConversationService(db_session).get_messages(uuid.uuid4(), user_id)

    def test_raises_for_other_users_conversation(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        other_user_id = db_session.execute(
            text("SELECT auth.create_user(:email, :password)"),
            {'email': 'other.messages@hirelume.com', 'password': 'password123'},
        ).scalar_one()
        other_conversation = Conversation(user_id=other_user_id, title='Not yours')
        db_session.add(other_conversation)
        db_session.commit()

        with pytest.raises(ConversationNotFoundError):
            ConversationService(db_session).get_messages(other_conversation.id, user_id)

class TestResolveConversation:
    def test_creates_new_conversation_when_none_given(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        conversation_id = ConversationService(db_session).resolve_conversation(
            None, user_id, 'A question that becomes the title'
        )

        conversation = db_session.get(Conversation, conversation_id)
        assert conversation is not None
        assert conversation.title == 'A question that becomes the title'

    def test_truncates_long_question_for_title(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        conversation_id = ConversationService(db_session).resolve_conversation(None, user_id, 'x' * 100)

        conversation = db_session.get(Conversation, conversation_id)
        assert len(conversation.title) == 60

    def test_returns_existing_conversation_id(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        existing = Conversation(user_id=user_id, title='Existing')
        db_session.add(existing)
        db_session.commit()

        conversation_id = ConversationService(db_session).resolve_conversation(existing.id, user_id, 'New question')

        assert conversation_id == existing.id

    def test_raises_for_unknown_conversation_id(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        with pytest.raises(ConversationNotFoundError):
            ConversationService(db_session).resolve_conversation(uuid.uuid4(), user_id, 'question')

class TestDeleteConversation:
    def test_deletes_own_conversation_and_cascades_messages(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        conversation = Conversation(user_id=user_id, title='To delete')
        db_session.add(conversation)
        db_session.flush()
        db_session.add(Message(conversation_id=conversation.id, role='user', content='Hi', created_at=datetime.now(timezone.utc)))
        db_session.commit()
        conversation_id = conversation.id

        ConversationService(db_session).delete_conversation(conversation_id, user_id)

        assert db_session.get(Conversation, conversation_id) is None
        remaining = db_session.execute(
            text('SELECT COUNT(*) FROM chat.messages WHERE conversation_id = :id'),
            {'id': conversation_id},
        ).scalar_one()
        assert remaining == 0

    def test_raises_for_unknown_conversation(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        with pytest.raises(ConversationNotFoundError):
            ConversationService(db_session).delete_conversation(uuid.uuid4(), user_id)

    def test_raises_for_other_users_conversation(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        other_user_id = db_session.execute(
            text("SELECT auth.create_user(:email, :password)"),
            {'email': 'other.delete@hirelume.com', 'password': 'password123'},
        ).scalar_one()
        other_conversation = Conversation(user_id=other_user_id, title='Not yours')
        db_session.add(other_conversation)
        db_session.commit()

        with pytest.raises(ConversationNotFoundError):
            ConversationService(db_session).delete_conversation(other_conversation.id, user_id)

class TestBuildHistory:
    def test_returns_messages_as_role_content_dicts(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        conversation = Conversation(user_id=user_id, title='Test')
        db_session.add(conversation)
        db_session.flush()
        db_session.add(Message(conversation_id=conversation.id, role='user', content='Hi', created_at=datetime.now(timezone.utc)))
        db_session.commit()

        history = ConversationService(db_session).build_history(conversation.id)

        assert history == [{'role': 'user', 'content': 'Hi'}]

@pytest.fixture
def real_conversation_id(engine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(conversation_service_module, 'SessionLocal', sessionmaker(bind=engine))

    with Session(engine) as session:
        user_id = session.execute(
            text("SELECT auth.create_user(:email, :password)"),
            {'email': 'ask-persist.tester@hirelume.com', 'password': 'password123'},
        ).scalar_one()
        conversation = Conversation(user_id=user_id, title='Test')
        session.add(conversation)
        session.commit()
        conversation_id = conversation.id

    yield conversation_id

    with Session(engine) as session:
        session.execute(text('DELETE FROM auth.users WHERE id = :id'), {'id': user_id})
        session.commit()

class TestAsk:
    @pytest.mark.anyio
    async def test_persists_the_question_then_yields_agent_events(
        self, db_session, real_conversation_id, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _fake_ask_agent(messages):
            yield {'type': 'answer', 'content': f'received {len(messages)} messages'}

        monkeypatch.setattr(conversation_service_module, 'ask_agent', _fake_ask_agent)

        events = [
            event async for event
            in ConversationService(db_session).ask(real_conversation_id, 'New question')
        ]

        assert events == [{'type': 'answer', 'content': 'received 1 messages'}]

        rows = db_session.execute(
            text('SELECT role, content FROM chat.messages WHERE conversation_id = :id'),
            {'id': real_conversation_id},
        ).all()
        assert [(r.role, r.content) for r in rows] == [('user', 'New question')]

    @pytest.mark.anyio
    async def test_persists_the_question_even_if_generation_fails(
        self, db_session, real_conversation_id, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _failing_ask_agent(messages):
            raise ConnectionError('client disconnected mid-stream')
            yield  # pragma: no cover - makes this an async generator

        monkeypatch.setattr(conversation_service_module, 'ask_agent', _failing_ask_agent)

        with pytest.raises(ConnectionError):
            async for _ in ConversationService(db_session).ask(real_conversation_id, 'A question'):
                pass

        rows = db_session.execute(
            text('SELECT role, content FROM chat.messages WHERE conversation_id = :id'),
            {'id': real_conversation_id},
        ).all()
        assert [(r.role, r.content) for r in rows] == [('user', 'A question')]

class TestAskAndPersist:
    @pytest.mark.anyio
    async def test_persists_both_messages_after_streaming(
        self, db_session, real_conversation_id, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _fake_ask_agent(messages):
            yield {'type': 'step', 'tool': 'query_database'}
            yield {'type': 'answer', 'content': 'The answer.'}

        monkeypatch.setattr(conversation_service_module, 'ask_agent', _fake_ask_agent)

        events = [
            event async for event
            in ConversationService(db_session).ask_and_persist(real_conversation_id, 'A question')
        ]

        assert [e['type'] for e in events] == ['step', 'answer']

        rows = db_session.execute(
            text('SELECT role, content FROM chat.messages WHERE conversation_id = :id ORDER BY created_at'),
            {'id': real_conversation_id},
        ).all()
        assert [(r.role, r.content) for r in rows] == [
            ('user', 'A question'),
            ('assistant', 'The answer.'),
        ]

    @pytest.mark.anyio
    async def test_persists_a_fallback_message_when_the_agent_yields_no_final_text(
        self, db_session, real_conversation_id, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Mirrors app/core/agent.py: if the agent's last turn is a tool call with no
        # accompanying text block, it yields an 'answer' event with empty content.
        async def _fake_ask_agent(messages):
            yield {'type': 'step', 'tool': 'generate_report'}
            yield {'type': 'answer', 'content': ''}

        monkeypatch.setattr(conversation_service_module, 'ask_agent', _fake_ask_agent)

        async for _ in ConversationService(db_session).ask_and_persist(real_conversation_id, 'A question'):
            pass

        rows = db_session.execute(
            text('SELECT role, content FROM chat.messages WHERE conversation_id = :id ORDER BY created_at'),
            {'id': real_conversation_id},
        ).all()
        assert [(r.role, r.content) for r in rows] == [
            ('user', 'A question'),
            ('assistant', conversation_service_module.FALLBACK_ANSWER),
        ]
