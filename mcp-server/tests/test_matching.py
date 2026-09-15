import uuid
from typing import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.matching import match_candidate
from tests.conftest import _basis_vector, _vector_literal

pytestmark = pytest.mark.usefixtures('_patch_engine')

@pytest.fixture
def seeded_match(admin_engine: Engine) -> Generator[dict, None, None]:
    cv_id = str(uuid.uuid4())
    with admin_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO documents.candidate_cv (id, candidate_name, content, file_path, embedding)
                VALUES (:id, :name, :content, :file_path, (:embedding)::vector)
            """),
            {
                'id': cv_id,
                'name': 'Jane Doe',
                'content': 'Experienced backend developer',
                'file_path': '/tmp/jane-doe-cv.pdf',
                'embedding': _vector_literal(_basis_vector(0)),
            },
        )
        job_requirement_id = conn.execute(
            text("""
                INSERT INTO documents.job_requirements (title, content, embedding)
                VALUES (:title, :content, (:embedding)::vector)
                RETURNING id
            """),
            {
                'title': 'Backend Engineer',
                'content': 'Looking for a backend engineer',
                'embedding': _vector_literal(_basis_vector(0)),
            },
        ).scalar_one()

    yield {'cv_id': cv_id, 'job_requirement_id': job_requirement_id}

    with admin_engine.begin() as conn:
        conn.execute(text('DELETE FROM documents.candidate_cv WHERE id = (:id)::uuid'), {'id': cv_id})
        conn.execute(text('DELETE FROM documents.job_requirements WHERE id = :id'), {'id': job_requirement_id})


class TestMatchCandidate:
    def test_returns_match_with_zero_distance_for_identical_embeddings(self, seeded_match: dict) -> None:
        result = match_candidate(seeded_match['cv_id'], seeded_match['job_requirement_id'])

        assert result['candidate_name'] == 'Jane Doe'
        assert result['vacancy_title'] == 'Backend Engineer'
        assert result['distance'] == pytest.approx(0.0, abs=1e-6)

    def test_raises_for_unknown_cv(self, seeded_match: dict) -> None:
        with pytest.raises(ValueError, match='not found'):
            match_candidate(str(uuid.uuid4()), seeded_match['job_requirement_id'])

    def test_raises_for_unknown_job_requirement(self, seeded_match: dict) -> None:
        with pytest.raises(ValueError, match='not found'):
            match_candidate(seeded_match['cv_id'], 999999)
