import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.db import get_db
from app.core.deps import get_current_user
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenPairResponse,
    UserResponse
)
from app.auth.service import (
    AuthService,
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidRefreshTokenError
)

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/login', response_model=TokenPairResponse)
@limiter.limit('5/minute')
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    try:
        return AuthService(db).login(payload.email, payload.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

@router.post('/refresh', response_model=TokenPairResponse)
@limiter.limit('5/minute')
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    try:
        return AuthService(db).refresh(payload.refresh_token)
    except InvalidRefreshTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    AuthService(db).logout(payload.refresh_token)

@router.get('/me', response_model=UserResponse)
def get_me(user_id: str = Depends(get_current_user), db: Session = Depends(get_db),) -> UserResponse:
        try:
            return AuthService(db).get_me(uuid.UUID(user_id))
        except UserNotFoundError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User no longer exists')
