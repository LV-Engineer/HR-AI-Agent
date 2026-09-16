import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.candidate_cv import CandidateCV
from app.services import candidate as candidate_service_module
from app.services.candidate import CandidateCVNotFoundError, CandidateService, UnsupportedFileTypeError
from tests.conftest import _sample_pdf_bytes


def _user_id(db_session: Session, email: str) -> uuid.UUID:
    return db_session.execute(
        text('SELECT id FROM auth.users WHERE email = :email'), {'email': email}
    ).scalar_one()


def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestUploadCv:
    def test_stores_file_and_returns_response(
        self, db_session, test_user, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)
        monkeypatch.setattr(candidate_service_module, 'get_embedding', _fake_embedding)

        response = CandidateService(db_session).upload_cv(
            candidate_name='Jane Doe',
            filename='cv.pdf',
            file_bytes=_sample_pdf_bytes(),
            uploaded_by=user_id,
        )

        assert response.candidate_name == 'Jane Doe'
        stored = db_session.get(CandidateCV, response.id)
        assert stored is not None
        assert Path(stored.file_path).exists()

    def test_raises_for_non_pdf_filename(self, db_session, test_user) -> None:
        email, _ = test_user
        user_id = _user_id(db_session, email)

        with pytest.raises(UnsupportedFileTypeError):
            CandidateService(db_session).upload_cv(
                candidate_name='Jane Doe', filename='cv.docx', file_bytes=b'x', uploaded_by=user_id,
            )


class TestListCvs:
    def test_returns_all_newest_first(self, db_session) -> None:
        now = datetime.now(timezone.utc)
        db_session.add(CandidateCV(candidate_name='Older', file_path='/tmp/older.pdf', uploaded_at=now - timedelta(minutes=5)))
        db_session.add(CandidateCV(candidate_name='Newer', file_path='/tmp/newer.pdf', uploaded_at=now))
        db_session.commit()

        result = CandidateService(db_session).list_cvs()

        assert [c.candidate_name for c in result] == ['Newer', 'Older']


class TestGetCvFile:
    def test_returns_path_and_name(self, db_session) -> None:
        cv = CandidateCV(candidate_name='Jane Doe', file_path='/tmp/jane.pdf')
        db_session.add(cv)
        db_session.commit()

        path, name = CandidateService(db_session).get_cv_file(cv.id)

        assert path == Path('/tmp/jane.pdf')
        assert name == 'Jane Doe'

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(CandidateCVNotFoundError):
            CandidateService(db_session).get_cv_file(uuid.uuid4())


class TestDeleteCv:
    def test_removes_row_and_file(self, db_session, tmp_path) -> None:
        file_path = tmp_path / 'jane.pdf'
        file_path.write_bytes(b'%PDF-1.4 fake')
        cv = CandidateCV(candidate_name='Jane Doe', file_path=str(file_path))
        db_session.add(cv)
        db_session.commit()
        cv_id = cv.id

        CandidateService(db_session).delete_cv(cv_id)

        assert db_session.get(CandidateCV, cv_id) is None
        assert not file_path.exists()

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(CandidateCVNotFoundError):
            CandidateService(db_session).delete_cv(uuid.uuid4())