import uuid
from datetime import datetime, timedelta, timezone

from app.candidates.models import CandidateCV
from app.candidates import service as candidate_service_module
from tests.conftest import _login, _sample_pdf_bytes

def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestUploadCv:
    def test_uploads_cv_and_returns_metadata(self, client, test_user, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        monkeypatch.setattr(candidate_service_module, 'get_embedding', _fake_embedding)

        response = client.post(
            '/candidates/cv',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            data={'candidate_name': 'Jane Doe'},
            files={'file': ('cv.pdf', _sample_pdf_bytes(), 'application/pdf')},
        )

        assert response.status_code == 201
        body = response.json()
        assert body['candidate_name'] == 'Jane Doe'
        assert 'file_path' not in body

    def test_rejects_non_pdf_file(self, client, test_user, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        monkeypatch.setattr(candidate_service_module, 'get_embedding', _fake_embedding)

        response = client.post(
            '/candidates/cv',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            data={'candidate_name': 'Jane Doe'},
            files={'file': ('cv.txt', b'not a pdf', 'text/plain')},
        )

        assert response.status_code == 422

    def test_requires_authentication(self, client) -> None:
        response = client.post(
            '/candidates/cv',
            data={'candidate_name': 'Jane Doe'},
            files={'file': ('cv.pdf', _sample_pdf_bytes(), 'application/pdf')},
        )

        assert response.status_code == 401


class TestListCvs:
    def test_returns_all_newest_first(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        now = datetime.now(timezone.utc)
        db_session.add(CandidateCV(candidate_name='Older', file_path='/tmp/older.pdf', uploaded_at=now - timedelta(minutes=5)))
        db_session.add(CandidateCV(candidate_name='Newer', file_path='/tmp/newer.pdf', uploaded_at=now))
        db_session.commit()

        response = client.get('/candidates/cv', headers=headers)

        assert response.status_code == 200
        names = [c['candidate_name'] for c in response.json()]
        assert names == ['Newer', 'Older']

    def test_requires_authentication(self, client) -> None:
        response = client.get('/candidates/cv')

        assert response.status_code == 401


class TestViewCv:
    def test_returns_file_inline(self, client, test_user, db_session, tmp_path) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        file_path = tmp_path / 'stored.pdf'
        file_path.write_bytes(_sample_pdf_bytes())
        cv = CandidateCV(candidate_name='Jane Doe', file_path=str(file_path))
        db_session.add(cv)
        db_session.commit()

        response = client.get(f'/candidates/cv/{cv.id}', headers=headers)

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'inline' in response.headers['content-disposition']

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get(
            f'/candidates/cv/{uuid.uuid4()}',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.get(f'/candidates/cv/{uuid.uuid4()}')

        assert response.status_code == 401


class TestDeleteCv:
    def test_deletes_row_and_file(self, client, test_user, db_session, tmp_path) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        file_path = tmp_path / 'stored.pdf'
        file_path.write_bytes(_sample_pdf_bytes())
        cv = CandidateCV(candidate_name='Jane Doe', file_path=str(file_path))
        db_session.add(cv)
        db_session.commit()
        cv_id = cv.id

        response = client.delete(f'/candidates/cv/{cv_id}', headers=headers)

        assert response.status_code == 204
        assert db_session.get(CandidateCV, cv_id) is None
        assert not file_path.exists()

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.delete(
            f'/candidates/cv/{uuid.uuid4()}',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.delete(f'/candidates/cv/{uuid.uuid4()}')

        assert response.status_code == 401
