from datetime import datetime, timedelta, timezone

from sqlalchemy import select

import pytest

from app.core.security import hash_refresh_token, decode_access_token
from app.models.refresh_token import RefreshToken
from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserNotFoundError,
)

def _decode_user_id(access_token: str):
    import uuid
    return uuid.UUID(decode_access_token(access_token))

class TestLogin:
    def test_returns_token_pair_for_valid_credentials(self, db_session, test_user) -> None:
        email, password = test_user

        result = AuthService(db_session).login(email, password)

        assert result.access_token
        assert result.refresh_token

    def test_raises_for_wrong_password(self, db_session, test_user) -> None:
        email, _ = test_user

        with pytest.raises(InvalidCredentialsError):
            AuthService(db_session).login(email, 'wrong-password')

    def test_raises_for_unknown_email(self, db_session) -> None:
        with pytest.raises(InvalidCredentialsError):
            AuthService(db_session).login('nobody.nowhere@hirelume.dev', 'password123')

class TestGetMe:
    def test_returns_user_for_valid_id(self, db_session, test_user) -> None:
        email, password = test_user
        tokens = AuthService(db_session).login(email, password)
        user_id = _decode_user_id(tokens.access_token)

        result = AuthService(db_session).get_me(user_id)

        assert result.email == email

    def test_raises_for_unknown_id(self, db_session) -> None:
        import uuid

        with pytest.raises(UserNotFoundError):
            AuthService(db_session).get_me(uuid.uuid4())

class TestRefresh:
    def test_rotates_token_and_preserves_family(self, db_session, test_user) -> None:
        email, password = test_user
        first = AuthService(db_session).login(email, password)

        second = AuthService(db_session).refresh(first.refresh_token)

        assert second.refresh_token != first.refresh_token
        assert second.access_token != first.access_token

        first_hash = hash_refresh_token(first.refresh_token)
        second_hash = hash_refresh_token(second.refresh_token)
        first_row = db_session.scalar(select(RefreshToken).where(RefreshToken.token_hash == first_hash))
        second_row = db_session.scalar(select(RefreshToken).where(RefreshToken.token_hash == second_hash))
        assert first_row.family_id == second_row.family_id

    def test_raises_for_unknown_token(self, db_session) -> None:
        with pytest.raises(InvalidRefreshTokenError):
            AuthService(db_session).refresh('not-a-real-token')

    def test_raises_for_expired_token(self, db_session, test_user) -> None:
        email, password = test_user
        tokens = AuthService(db_session).login(email, password)

        stored = db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(tokens.refresh_token))
        )
        stored.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()

        with pytest.raises(InvalidRefreshTokenError):
            AuthService(db_session).refresh(tokens.refresh_token)

    def test_revokes_entire_family_on_reuse(self, db_session, test_user) -> None:
        email, password = test_user
        first = AuthService(db_session).login(email, password)
        second = AuthService(db_session).refresh(first.refresh_token)

        with pytest.raises(InvalidRefreshTokenError):
            AuthService(db_session).refresh(first.refresh_token)

        second_row = db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(second.refresh_token))
        )
        assert second_row.revoked_at is not None

class TestLogout:
    def test_revokes_valid_token(self, db_session, test_user) -> None:
        email, password = test_user
        tokens = AuthService(db_session).login(email, password)

        AuthService(db_session).logout(tokens.refresh_token)

        with pytest.raises(InvalidRefreshTokenError):
            AuthService(db_session).refresh(tokens.refresh_token)

    def test_is_idempotent_for_unknown_token(self, db_session) -> None:
        AuthService(db_session).logout('not-a-real-token')