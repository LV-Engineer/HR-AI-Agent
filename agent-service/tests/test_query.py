from unittest.mock import AsyncMock

import pytest

from app.api.routes import query as query_module
from tests.conftest import _login

class TestQuery:
    def test_returns_answer_for_authenticated_user(self, client, test_user, monkeypatch: pytest.MonkeyPatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        mock_ask_agent = AsyncMock(return_value='42 employees in total.')
        monkeypatch.setattr(query_module, 'ask_agent', mock_ask_agent)

        response = client.post(
            '/query',
            json={'question': 'How many employees do we have?'},
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 200
        assert response.json() == {'answer': '42 employees in total.'}
        mock_ask_agent.assert_called_once_with('How many employees do we have?')

    def test_requires_authentication(self, client) -> None:
        response = client.post('/query', json={'question': 'test'})

        assert response.status_code == 401