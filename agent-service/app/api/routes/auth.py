import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token, 
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPairResponse, UserResponse

router = APIRouter(prefix='/auth', tags=['auth'])

def _issue_token_pair(
    db: Session,
    user_id: uuid.UUID,
    family_id: uuid.UUID | None = None
) -> TokenPairResponse:
    access_token = create_access_token(subject=str(user_id))

    refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    db.add(RefreshToken(
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
    ))
    db.commit()

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)

@router.post('/login', response_model=TokenPairResponse)
@limiter.limit('5/minute')
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )
    return _issue_token_pair(db, user.id)

@router.post('/refresh', response_model=TokenPairResponse)
@limiter.limit('5/minute')
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)

    if stored is not None and stored.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == stored.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    if stored is None or stored.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    stored.revoked_at = now
    db.commit()

    return _issue_token_pair(db, stored.user_id, family_id=stored.family_id)

@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()
    
@router.get('/me', response_model=UserResponse)
def get_me(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User no longer exists'
        )
    return UserResponse.model_validate(user)