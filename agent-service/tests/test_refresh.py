from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_refresh_token
from app.models.refresh_token import RefreshToken

def _login(client, email, password):
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return response.json()

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
