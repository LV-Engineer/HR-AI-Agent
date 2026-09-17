from datetime import datetime, timedelta, timezone

import pytest

from app.models.job_requirement import JobRequirement
from app.services import job_requirement as job_requirement_service_module
from app.services.job_requirement import JobRequirementNotFoundError, JobRequirementService

def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestCreateJobRequirement:
    def test_stores_and_returns_response(self, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(job_requirement_service_module, 'get_embedding', _fake_embedding)

        response = JobRequirementService(db_session).create_job_requirement('Backend Developer', 'Looking for a dev.')

        assert response.title == 'Backend Developer'
        assert response.content == 'Looking for a dev.'
        stored = db_session.get(JobRequirement, response.id)
        assert stored is not None
        assert stored.embedding is not None


class TestListJobRequirements:
    def test_returns_all_newest_first(self, db_session) -> None:
        now = datetime.now(timezone.utc)
        db_session.add(JobRequirement(title='Older', content='...', created_at=now - timedelta(minutes=5)))
        db_session.add(JobRequirement(title='Newer', content='...', created_at=now))
        db_session.commit()

        result = JobRequirementService(db_session).list_job_requirements()

        assert [jr.title for jr in result] == ['Newer', 'Older']


class TestGetJobRequirement:
    def test_returns_full_response(self, db_session) -> None:
        jr = JobRequirement(title='Backend Developer', content='Looking for a dev.')
        db_session.add(jr)
        db_session.commit()

        response = JobRequirementService(db_session).get_job_requirement(jr.id)

        assert response.content == 'Looking for a dev.'

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(JobRequirementNotFoundError):
            JobRequirementService(db_session).get_job_requirement(999999)


class TestUpdateJobRequirement:
    def test_recomputes_embedding_when_content_changes(self, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []
        def _recording_embedding(content: str) -> list[float]:
            calls.append(content)
            return [1.0] * 1024
        monkeypatch.setattr(job_requirement_service_module, 'get_embedding', _recording_embedding)

        jr = JobRequirement(title='Backend Developer', content='Old text', embedding=[0.0] * 1024)
        db_session.add(jr)
        db_session.commit()

        response = JobRequirementService(db_session).update_job_requirement(jr.id, title=None, content='New text')

        assert response.content == 'New text'
        assert calls == ['New text']

    def test_does_not_recompute_embedding_when_only_title_changes(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []
        monkeypatch.setattr(
            job_requirement_service_module, 'get_embedding',
            lambda content: calls.append(content) or [1.0] * 1024,
        )

        jr = JobRequirement(title='Old title', content='Text', embedding=[0.0] * 1024)
        db_session.add(jr)
        db_session.commit()

        response = JobRequirementService(db_session).update_job_requirement(jr.id, title='New title', content=None)

        assert response.title == 'New title'
        assert calls == []

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(JobRequirementNotFoundError):
            JobRequirementService(db_session).update_job_requirement(999999, title='x', content=None)


class TestDeleteJobRequirement:
    def test_removes_row(self, db_session) -> None:
        jr = JobRequirement(title='Backend Developer', content='...')
        db_session.add(jr)
        db_session.commit()
        jr_id = jr.id

        JobRequirementService(db_session).delete_job_requirement(jr_id)

        assert db_session.get(JobRequirement, jr_id) is None

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(JobRequirementNotFoundError):
            JobRequirementService(db_session).delete_job_requirement(999999)