import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, generate_refresh_token, hash_refresh_token, verify_password
from app.auth.repositories import RefreshTokenRepository, UserRepository
from app.auth.schemas import TokenPairResponse, UserResponse

class InvalidCredentialsError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class InvalidRefreshTokenError(Exception):
    pass

class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._refresh_tokens = RefreshTokenRepository(db)

    def login(self, email: str, password: str) -> TokenPairResponse:
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return self._issue_token_pair(user.id)

    def get_me(self, user_id: uuid.UUID) -> UserResponse:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserResponse.model_validate(user)

    def logout(self, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored = self._refresh_tokens.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            self._db.commit()

    def refresh(self, refresh_token: str) -> TokenPairResponse:
        token_hash = hash_refresh_token(refresh_token)
        stored = self._refresh_tokens.get_by_hash(token_hash)
        now = datetime.now(timezone.utc)

        if stored is not None and stored.revoked_at is not None:
            self._refresh_tokens.revoke_family(stored.family_id, now)
            self._db.commit()
            raise InvalidRefreshTokenError()

        if stored is None or stored.expires_at < now:
            raise InvalidRefreshTokenError()

        stored.revoked_at = now
        return self._issue_token_pair(stored.user_id, stored.family_id)

    def _issue_token_pair(self, user_id: uuid.UUID, family_id: uuid.UUID | None = None) -> TokenPairResponse:
        access_token = create_access_token(subject=str(user_id))

        refresh_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        self._refresh_tokens.create(
            user_id=user_id,
            family_id=family_id or uuid.uuid4(),
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
        self._db.commit()

        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
