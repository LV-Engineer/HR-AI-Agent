from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.policies.models import HrPolicy
from app.policies import service as policy_service_module
from app.policies.service import HrPolicyNotFoundError, PolicyService, UnsupportedFileTypeError
from tests.conftest import _sample_pdf_bytes

def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestUploadPolicy:
    def test_stores_file_and_returns_response(self, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(policy_service_module, 'get_embedding', _fake_embedding)

        response = PolicyService(db_session).upload_policy(
            title='Vacation Policy', filename='policy.pdf', file_bytes=_sample_pdf_bytes(),
        )

        assert response.title == 'Vacation Policy'
        stored = db_session.get(HrPolicy, response.id)
        assert stored is not None
        assert stored.file_path is not None
        assert Path(stored.file_path).exists()

    def test_raises_for_non_pdf_filename(self, db_session) -> None:
        with pytest.raises(UnsupportedFileTypeError):
            PolicyService(db_session).upload_policy(
                title='Vacation Policy', filename='policy.docx', file_bytes=b'x',
            )


class TestListPolicies:
    def test_returns_all_newest_first(self, db_session) -> None:
        now = datetime.now(timezone.utc)
        db_session.add(HrPolicy(title='Older', content='...', created_at=now - timedelta(minutes=5)))
        db_session.add(HrPolicy(title='Newer', content='...', created_at=now))
        db_session.commit()

        result = PolicyService(db_session).list_policies()

        assert [p.title for p in result] == ['Newer', 'Older']


class TestGetPolicyFile:
    def test_returns_path_and_title(self, db_session) -> None:
        policy = HrPolicy(title='Vacation Policy', content='...', file_path='/tmp/policy.pdf')
        db_session.add(policy)
        db_session.commit()

        path, title = PolicyService(db_session).get_policy_file(policy.id)

        assert path == Path('/tmp/policy.pdf')
        assert title == 'Vacation Policy'

    def test_raises_for_policy_without_file(self, db_session) -> None:
        policy = HrPolicy(title='Legacy policy', content='...')
        db_session.add(policy)
        db_session.commit()

        with pytest.raises(HrPolicyNotFoundError):
            PolicyService(db_session).get_policy_file(policy.id)

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(HrPolicyNotFoundError):
            PolicyService(db_session).get_policy_file(999999)


class TestDeletePolicy:
    def test_removes_row_and_file(self, db_session, tmp_path) -> None:
        file_path = tmp_path / 'policy.pdf'
        file_path.write_bytes(b'%PDF-1.4 fake')
        policy = HrPolicy(title='Vacation Policy', content='...', file_path=str(file_path))
        db_session.add(policy)
        db_session.commit()
        policy_id = policy.id

        PolicyService(db_session).delete_policy(policy_id)

        assert db_session.get(HrPolicy, policy_id) is None
        assert not file_path.exists()

    def test_removes_row_when_no_file(self, db_session) -> None:
        policy = HrPolicy(title='Legacy policy', content='...')
        db_session.add(policy)
        db_session.commit()
        policy_id = policy.id

        PolicyService(db_session).delete_policy(policy_id)

        assert db_session.get(HrPolicy, policy_id) is None

    def test_raises_for_unknown_id(self, db_session) -> None:
        with pytest.raises(HrPolicyNotFoundError):
            PolicyService(db_session).delete_policy(999999)
