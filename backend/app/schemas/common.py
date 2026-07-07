from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "ok"
    request_id: str = "local"


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    data: None = None
    message: str
    request_id: str
    error_code: ErrorCode
    details: dict | None = None
