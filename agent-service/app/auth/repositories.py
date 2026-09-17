import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.models import RefreshToken, User

class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._db.scalar(select(User).where(User.id == user_id))

class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, user_id: uuid.UUID, family_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None:
        self._db.add(RefreshToken(
            user_id=user_id, family_id=family_id, token_hash=token_hash, expires_at=expires_at
        ))

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self._db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    def revoke_family(self, family_id: uuid.UUID, revoked_at: datetime) -> None:
        self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
