from unittest.mock import MagicMock

import httpx
import pytest

from app.core.config import settings
from app.core.embeddings import get_embedding

class TestGetEmbedding:
    def test_returns_embedding_from_reponse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {'embedding': [0.1, 0.2, 0.3]}
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, 'post', mock_post)

        result = get_embedding('vacation policy')
        assert result == [0.1, 0.2, 0.3]

    def test_sends_correct_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {'embedding': []}
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, 'post', mock_post)

        get_embedding('vacation policy')

        mock_post.assert_called_once_with(
            f'{settings.ollama_url}/api/embeddings',
            json={'model': settings.embedding_model, 'prompt': 'vacation policy'},
            timeout=60.0,
        )

    def test_raises_on_http_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'error', request=MagicMock(), response=mock_response
        )
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, 'post', mock_post)

        with pytest.raises(httpx.HTTPStatusError):
            get_embedding('vacation policy')