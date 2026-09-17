from datetime import datetime, timedelta, timezone

from app.job_requirements.models import JobRequirement
from app.job_requirements import service as job_requirement_service_module
from tests.conftest import _login

def _fake_embedding(_content: str) -> list[float]:
    return [0.0] * 1024


class TestCreateJobRequirement:
    def test_creates_and_returns_full_response(self, client, test_user, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        monkeypatch.setattr(job_requirement_service_module, 'get_embedding', _fake_embedding)

        response = client.post(
            '/job-requirements',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            json={'title': 'Backend Developer', 'content': 'Looking for a Python developer.'},
        )

        assert response.status_code == 201
        body = response.json()
        assert body['title'] == 'Backend Developer'
        assert body['content'] == 'Looking for a Python developer.'

    def test_requires_authentication(self, client) -> None:
        response = client.post('/job-requirements', json={'title': 'x', 'content': 'y'})

        assert response.status_code == 401


class TestListJobRequirements:
    def test_returns_summaries_newest_first(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        now = datetime.now(timezone.utc)
        db_session.add(JobRequirement(title='Older', content='...', created_at=now - timedelta(minutes=5)))
        db_session.add(JobRequirement(title='Newer', content='...', created_at=now))
        db_session.commit()

        response = client.get('/job-requirements', headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert [jr['title'] for jr in body] == ['Newer', 'Older']
        assert 'content' not in body[0]

    def test_requires_authentication(self, client) -> None:
        response = client.get('/job-requirements')

        assert response.status_code == 401


class TestGetJobRequirement:
    def test_returns_full_detail(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        jr = JobRequirement(title='Backend Developer', content='Looking for a Python developer.')
        db_session.add(jr)
        db_session.commit()

        response = client.get(f'/job-requirements/{jr.id}', headers=headers)

        assert response.status_code == 200
        assert response.json()['content'] == 'Looking for a Python developer.'

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get(
            '/job-requirements/999999', headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.get('/job-requirements/1')

        assert response.status_code == 401


class TestUpdateJobRequirement:
    def test_updates_content_and_recomputes_embedding(self, client, test_user, db_session, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        calls: list[str] = []
        def _recording_embedding(content: str) -> list[float]:
            calls.append(content)
            return [0.0] * 1024
        monkeypatch.setattr(job_requirement_service_module, 'get_embedding', _recording_embedding)

        jr = JobRequirement(title='Backend Developer', content='Old text', embedding=[0.0] * 1024)
        db_session.add(jr)
        db_session.commit()

        response = client.patch(
            f'/job-requirements/{jr.id}', headers=headers, json={'content': 'New text'},
        )

        assert response.status_code == 200
        assert response.json()['content'] == 'New text'
        assert calls == ['New text']

    def test_updates_title_only_without_recomputing_embedding(self, client, test_user, db_session, monkeypatch) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        calls: list[str] = []
        monkeypatch.setattr(
            job_requirement_service_module, 'get_embedding',
            lambda content: calls.append(content) or [0.0] * 1024,
        )

        jr = JobRequirement(title='Old title', content='Text', embedding=[0.0] * 1024)
        db_session.add(jr)
        db_session.commit()

        response = client.patch(
            f'/job-requirements/{jr.id}', headers=headers, json={'title': 'New title'},
        )

        assert response.status_code == 200
        assert response.json()['title'] == 'New title'
        assert calls == []

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.patch(
            '/job-requirements/999999',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'},
            json={'title': 'x'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.patch('/job-requirements/1', json={'title': 'x'})

        assert response.status_code == 401


class TestDeleteJobRequirement:
    def test_deletes_row(self, client, test_user, db_session) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        jr = JobRequirement(title='Backend Developer', content='...')
        db_session.add(jr)
        db_session.commit()
        jr_id = jr.id

        response = client.delete(f'/job-requirements/{jr_id}', headers=headers)

        assert response.status_code == 204
        assert db_session.get(JobRequirement, jr_id) is None

    def test_returns_404_for_unknown_id(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.delete(
            '/job-requirements/999999', headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.delete('/job-requirements/1')

        assert response.status_code == 401
