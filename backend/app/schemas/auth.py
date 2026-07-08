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
    email: DevelopmentEmailStr
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
