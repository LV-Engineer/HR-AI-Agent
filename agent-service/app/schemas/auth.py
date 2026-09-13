import uuid
import re
from datetime import datetime

from pydantic import BaseModel, field_validator, ConfigDict

from app.core.config import settings

EMAIL_PATTERN = re.compile(rf'^[a-z]+\.[a-z]+@{re.escape(settings.company_email_domain)}$')

class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError(f"Email must match format 'name.surname@{settings.company_email_domain}'")
        return value

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime

class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshRequest(BaseModel):
    refresh_token: str