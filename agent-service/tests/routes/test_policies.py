from datetime import datetime, timedelta, timezone

from app.models.hr_policy import HrPolicy
from app.services import policy as policy_service_module
from tests.conftest import _login, _sample_pdf_bytes

def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestUploadPolicy:
    def test_uploads_policy_and_returns_metadata(self, client, test_user, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        monkeypatch.setattr(policy_service_module, 'get_embedding', _fake_embedding)

        response = client.post(
            '/policies',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            data={'title': 'Vacation Policy'},
            files={'file': ('policy.pdf', _sample_pdf_bytes(), 'application/pdf')},
        )

        assert response.status_code == 201
        body = response.json()
        assert body['title'] == 'Vacation Policy'
        assert 'file_path' not in body

    def test_rejects_non_pdf_file(self, client, test_user, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        monkeypatch.setattr(policy_service_module, 'get_embedding', _fake_embedding)

        response = client.post(
            '/policies',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            data={'title': 'Vacation Policy'},
            files={'file': ('policy.txt', b'not a pdf', 'text/plain')},
        )

        assert response.status_code == 422

    def test_requires_authentication(self, client) -> None:
        response = client.post(
            '/policies',
            data={'title': 'Vacation Policy'},
            files={'file': ('policy.pdf', _sample_pdf_bytes(), 'application/pdf')},
        )

        assert response.status_code == 401


class TestListPolicies:
    def test_returns_all_newest_first(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        now = datetime.now(timezone.utc)
        db_session.add(HrPolicy(title='Older', content='...', created_at=now - timedelta(minutes=5)))
        db_session.add(HrPolicy(title='Newer', content='...', created_at=now))
        db_session.commit()

        response = client.get('/policies', headers=headers)

        assert response.status_code == 200
        titles = [p['title'] for p in response.json()]
        assert titles == ['Newer', 'Older']

    def test_requires_authentication(self, client) -> None:
        response = client.get('/policies')

        assert response.status_code == 401


class TestViewPolicy:
    def test_returns_file_inline(self, client, test_user, db_session, tmp_path) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        file_path = tmp_path / 'stored.pdf'
        file_path.write_bytes(_sample_pdf_bytes())
        policy = HrPolicy(title='Vacation Policy', content='...', file_path=str(file_path))
        db_session.add(policy)
        db_session.commit()

        response = client.get(f'/policies/{policy.id}', headers=headers)

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'inline' in response.headers['content-disposition']

    def test_returns_404_for_policy_without_file(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        policy = HrPolicy(title='Legacy policy', content='...')
        db_session.add(policy)
        db_session.commit()

        response = client.get(f'/policies/{policy.id}', headers=headers)

        assert response.status_code == 404

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get(
            '/policies/999999',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.get('/policies/1')

        assert response.status_code == 401


class TestDeletePolicy:
    def test_deletes_row_and_file(self, client, test_user, db_session, tmp_path) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        file_path = tmp_path / 'stored.pdf'
        file_path.write_bytes(_sample_pdf_bytes())
        policy = HrPolicy(title='Vacation Policy', content='...', file_path=str(file_path))
        db_session.add(policy)
        db_session.commit()
        policy_id = policy.id

        response = client.delete(f'/policies/{policy_id}', headers=headers)

        assert response.status_code == 204
        assert db_session.get(HrPolicy, policy_id) is None
        assert not file_path.exists()

    def test_deletes_legacy_policy_without_file(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        policy = HrPolicy(title='Legacy policy', content='...')
        db_session.add(policy)
        db_session.commit()
        policy_id = policy.id

        response = client.delete(f'/policies/{policy_id}', headers=headers)

        assert response.status_code == 204
        assert db_session.get(HrPolicy, policy_id) is None

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.delete(
            '/policies/999999',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.delete('/policies/1')

        assert response.status_code == 401