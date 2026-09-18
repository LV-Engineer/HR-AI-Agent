from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from app.conversations.models import Conversation, Message
from tests.conftest import _login

class TestListConversations:
    def test_returns_only_own_conversations_newest_first(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        user_id = db_session.execute(
            text('SELECT id FROM auth.users WHERE email = :email'), {'email': email}
        ).scalar_one()

        other_user_id = db_session.execute(
            text("SELECT auth.create_user(:email, :password)"),
            {'email': 'other.user@hirelume.dev', 'password': 'password123'},
        ).scalar_one()

        now = datetime.now(timezone.utc)
        db_session.add(Conversation(user_id=user_id, title='Older', created_at=now - timedelta(minutes=5)))
        db_session.add(Conversation(user_id=user_id, title='Newer', created_at=now))
        db_session.add(Conversation(user_id=other_user_id, title='Not mine', created_at=now))
        db_session.commit()

        response = client.get('/conversations', headers=headers)

        assert response.status_code == 200
        titles = [c['title'] for c in response.json()]
        assert titles == ['Newer', 'Older']

    def test_requires_authentication(self, client) -> None:
        response = client.get('/conversations')

        assert response.status_code == 401


class TestDeleteConversation:
    def test_deletes_own_conversation(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        user_id = db_session.execute(
            text('SELECT id FROM auth.users WHERE email = :email'), {'email': email}
        ).scalar_one()
        conversation = Conversation(user_id=user_id, title='To delete')
        db_session.add(conversation)
        db_session.commit()

        response = client.delete(f'/conversations/{conversation.id}', headers=headers)

        assert response.status_code == 204

    def test_returns_404_for_unknown_conversation(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.delete(
            '/conversations/00000000-0000-0000-0000-000000000000',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.delete('/conversations/00000000-0000-0000-0000-000000000000')

        assert response.status_code == 401

class TestGetConversationMessages:
    def test_returns_messages_in_order(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        user_id = db_session.execute(
            text('SELECT id FROM auth.users WHERE email = :email'), {'email': email}
        ).scalar_one()

        conversation = Conversation(user_id=user_id, title='Test conversation')
        db_session.add(conversation)
        db_session.flush()
        db_session.add(Message(conversation_id=conversation.id, role='user', content='Hi'))
        db_session.add(Message(conversation_id=conversation.id, role='assistant', content='Hello'))
        db_session.commit()

        response = client.get(f'/conversations/{conversation.id}/messages', headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert [(m['role'], m['content']) for m in body] == [('user', 'Hi'), ('assistant', 'Hello')]

    def test_returns_404_for_unknown_conversation(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get(
            '/conversations/00000000-0000-0000-0000-000000000000/messages',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.get('/conversations/00000000-0000-0000-0000-000000000000/messages')

        assert response.status_code == 401
