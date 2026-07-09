from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import DevelopmentEmailStr


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: DevelopmentEmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"


class UserLogin(BaseModel):
    username_or_email: str = Field(min_length=2, max_length=128)
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: DevelopmentEmailStr
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: DevelopmentEmailStr


class PasswordResetVerify(BaseModel):
    token: str = Field(min_length=1, max_length=255)


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=6, max_length=128, description="New password (min 6 characters)")


class PasswordResetVerifyResponse(BaseModel):
    valid: bool
    email_partial: str | None = None
    error: str | None = None


class PasswordResetResponse(BaseModel):
    success: bool
    error: str | None = None


class UserUpdate(BaseModel):
    status: str | None = None  # "active", "suspended"
    role: str | None = None     # "user", "admin"
