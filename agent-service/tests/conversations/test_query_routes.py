import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.conversations import service as conversation_service_module
from app.core.db import get_db
from app.main import app
from tests.conftest import _login

TEST_EMAIL = 'query.tester@hirelume.com'
TEST_PASSWORD = 'password123'

@pytest.fixture
def real_client(engine, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(conversation_service_module, 'SessionLocal', sessionmaker(bind=engine))

    with Session(engine) as session:
        session.execute(
            text('SELECT auth.create_user(:email, :password)'),
            {'email': TEST_EMAIL, 'password': TEST_PASSWORD},
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

    with Session(engine) as session:
        session.execute(text('DELETE FROM auth.users WHERE email = :email'), {'email': TEST_EMAIL})
        session.commit()

async def _fake_ask_agent(_messages):
    yield {'type': 'step', 'tool': 'query_database'}
    yield {'type': 'answer', 'content': '42 employees in total.'}

def _parse_sse_events(body: str) -> list[dict]:
    events = []
    for chunk in body.strip().split('\n\n'):
        if not chunk:
            continue
        assert chunk.startswith('data: ')
        events.append(json.loads(chunk.removeprefix('data: ')))
    return events

class TestQuery:
    def test_streams_step_and_answer_events(self, real_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        tokens = _login(real_client, TEST_EMAIL, TEST_PASSWORD)
        monkeypatch.setattr(conversation_service_module, 'ask_agent', _fake_ask_agent)

        response = real_client.post(
            '/query',
            json={'question': 'How many employees do we have?'},
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        assert events[0]['type'] == 'step'
        assert events[0]['tool'] == 'query_database'
        assert events[1]['type'] == 'answer'
        assert events[1]['content'] == '42 employees in total.'
        assert events[0]['conversation_id'] == events[1]['conversation_id']

    def test_persists_messages_after_streaming(
        self, real_client: TestClient, engine, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tokens = _login(real_client, TEST_EMAIL, TEST_PASSWORD)
        monkeypatch.setattr(conversation_service_module, 'ask_agent', _fake_ask_agent)

        response = real_client.post(
            '/query',
            json={'question': 'How many employees do we have?'},
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )
        conversation_id = _parse_sse_events(response.text)[0]['conversation_id']

        with Session(engine) as session:
            rows = session.execute(
                text('SELECT role, content FROM chat.messages WHERE conversation_id = :id ORDER BY created_at'),
                {'id': conversation_id},
            ).all()

        assert [(r.role, r.content) for r in rows] == [
            ('user', 'How many employees do we have?'),
            ('assistant', '42 employees in total.'),
        ]

    def test_sends_full_history_to_agent(self, real_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        tokens = _login(real_client, TEST_EMAIL, TEST_PASSWORD)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        calls: list[list[dict]] = []

        async def _recording_ask_agent(messages):
            calls.append(messages)
            answer = 'First answer.' if len(calls) == 1 else 'Second answer.'
            yield {'type': 'answer', 'content': answer}

        monkeypatch.setattr(conversation_service_module, 'ask_agent', _recording_ask_agent)

        first = real_client.post('/query', json={'question': 'First question?'}, headers=headers)
        conversation_id = _parse_sse_events(first.text)[0]['conversation_id']

        real_client.post(
            '/query',
            json={'question': 'Second question?', 'conversation_id': conversation_id},
            headers=headers,
        )

        assert calls[1] == [
            {'role': 'user', 'content': 'First question?'},
            {'role': 'assistant', 'content': 'First answer.'},
            {'role': 'user', 'content': 'Second question?'},
        ]

    def test_rejects_conversation_belonging_to_another_user(self, real_client: TestClient, engine) -> None:
        tokens = _login(real_client, TEST_EMAIL, TEST_PASSWORD)

        with Session(engine) as session:
            other_user_id = session.execute(
                text("SELECT auth.create_user(:email, :password)"),
                {'email': 'other.query.tester@hirelume.com', 'password': 'password123'},
            ).scalar_one()
            other_conversation_id = session.execute(
                text('INSERT INTO chat.conversations (user_id, title) VALUES (:user_id, :title) RETURNING id'),
                {'user_id': other_user_id, 'title': 'Not yours'},
            ).scalar_one()
            session.commit()

        response = real_client.post(
            '/query',
            json={'question': 'test', 'conversation_id': str(other_conversation_id)},
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

        with Session(engine) as session:
            session.execute(
                text('DELETE FROM auth.users WHERE email = :email'),
                {'email': 'other.query.tester@hirelume.com'},
            )
            session.commit()

    def test_requires_authentication(self, real_client: TestClient) -> None:
        response = real_client.post('/query', json={'question': 'test'})

        assert response.status_code == 401
