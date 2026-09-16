from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.core.security import hash_refresh_token
from app.models.refresh_token import RefreshToken


def _login(client, email, password):
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return response.json()

class TestLogin:
    def test_login_success(self, client, test_user):
        email, password = test_user

        response = client.post('/auth/login', json={'email': email, 'password': password})

        assert response.status_code == 200
        body = response.json()
        assert 'access_token' in body
        assert 'refresh_token' in body

    def test_login_wrong_password(self, client):
        response = client.post('/auth/login', json={'email': 'test.user@hirelume.dev', 'password': 'wrong'})

        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        response = client.post('/auth/login', json={'email': 'nobody.nowhere@hirelume.dev', 'password': 'password123'})

        assert response.status_code == 401

    def test_login_malformed_email_rejected(self, client):
        response = client.post('/auth/login', json={'email': 'not-a-valid-email', 'password': 'password123'})

        assert response.status_code == 422

class TestMe:
    def test_me_with_valid_token(self, client, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get('/auth/me', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

        assert response.status_code == 200
        assert response.json()['email'] == email

    def test_me_missing_token(self, client):
        response = client.get('/auth/me')

        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        response = client.get('/auth/me', headers={'Authorization': 'Bearer not-a-real-token'})

        assert response.status_code == 401

    def test_me_deleted_user(self, client, db_session, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        db_session.execute(text('DELETE FROM auth.users WHERE email = :email'), {'email': email})
        db_session.commit()

        response = client.get('/auth/me', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

        assert response.status_code == 401
        assert response.json()['detail'] == 'User no longer exists'


class TestLogout:
    def test_logout_revokes_refresh_token(self, client, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.post('/auth/logout', json={'refresh_token': tokens['refresh_token']})
        assert response.status_code == 204

        reused = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})
        assert reused.status_code == 401

class TestRefresh:
    def test_refresh_rotates_token(self, client, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})

        assert response.status_code == 200
        new_tokens = response.json()
        assert new_tokens['refresh_token'] != tokens['refresh_token']
        assert new_tokens['access_token'] != tokens['access_token']

    def test_refresh_reuse_revokes_family(self, client, db_session, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        first = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})
        assert first.status_code == 200

        reused = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})
        assert reused.status_code == 401

        new_refresh_token = first.json()['refresh_token']
        stored = db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(new_refresh_token))
        )
        assert stored is not None
        assert stored.revoked_at is not None

    def test_refresh_invalid_token(self, client):
        response = client.post('/auth/refresh', json={'refresh_token': 'not-a-real-token'})

        assert response.status_code == 401

    def test_refresh_expired_token(self, client, db_session, test_user):
        email, password = test_user
        tokens = _login(client, email, password)

        stored = db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(tokens['refresh_token']))
        )
        stored.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()

        response = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})

        assert response.status_code == 401
