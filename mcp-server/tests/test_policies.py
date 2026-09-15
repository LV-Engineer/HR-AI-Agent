from typing import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core import policies as policies_module
from app.core.policies import search_hr_policies
from tests.conftest import _basis_vector, _vector_literal

pytestmark = pytest.mark.usefixtures('_patch_engine')

@pytest.fixture
def seeded_policies(admin_engine: Engine) -> Generator[None, None, None]:
    with admin_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO documents.hr_policies (title, content, embedding)
                VALUES (:title, :content, (:embedding)::vector)
            """),
            [
                {'title': 'Vacation Policy', 'content': 'Vacation policy content', 'embedding': _vector_literal(_basis_vector(0))},
                {'title': 'Remote Work Policy', 'content': 'Remote work policy content', 'embedding': _vector_literal(_basis_vector(1))},
                {'title': 'Sick Leave Policy', 'content': 'Sick leave policy content', 'embedding': _vector_literal(_basis_vector(2))},
            ],
        )
    yield
    with admin_engine.begin() as conn:
        conn.execute(text('DELETE FROM documents.hr_policies'))

class TestSearchHrPolicies:
    def test_orders_by_similarity(self, seeded_policies: None, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(policies_module, 'get_embedding', lambda _: _basis_vector(0))

        results = search_hr_policies('vacation days')

        assert results[0]['title'] == 'Vacation Policy'
        assert results[0]['distance'] == pytest.approx(0.0, abs=1e-6)
        assert {r['title'] for r in results[1:]} == {'Remote Work Policy', 'Sick Leave Policy'}

    def test_respects_limit(self, seeded_policies: None, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(policies_module, 'get_embedding', lambda _: _basis_vector(0))

        results = search_hr_policies('vacation days', limit=1)

        assert len(results) == 1

    def test_calls_embedding_with_query_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_embed = MagicMock(return_value=_basis_vector(0))
        monkeypatch.setattr(policies_module, 'get_embedding', mock_embed)

        search_hr_policies('vacation days')

        mock_embed.assert_called_once_with('vacation days')