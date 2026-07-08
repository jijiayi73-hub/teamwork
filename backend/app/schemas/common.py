from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel
from email_validator import validate_email as _validate_email, EmailNotValidError

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


def validate_email_with_local_domains(email: str) -> str:
    """
    Custom email validator that allows .local, .localhost, .test domains for development.

    This validator extends Pydantic's EmailStr behavior to permit reserved/special-use
    domains that are typically rejected by RFC-compliant validators, which is useful
    for local development and demo environments.

    Args:
        email: The email address to validate

    Returns:
        The normalized email address (lowercase)

    Raises:
        ValueError: If the email format is invalid
    """
    email_lower = email.lower()
    allowed_dev_domains = {".local", ".localhost", ".test", ".example", ".invalid"}

    # Check if it's a development domain we want to allow FIRST
    # This avoids the reserved domain error from standard validation
    if any(email_lower.endswith(domain) for domain in allowed_dev_domains):
        # Basic format check for development emails
        if "@" not in email or email.count("@") != 1:
            raise ValueError("An email address must have an @-sign.")

        local, domain = email_lower.rsplit("@", 1)
        if not local or not domain or "." not in domain:
            raise ValueError("Invalid email format")

        # Normalize and return (already lowercase)
        return f"{local}@{domain}"

    # For non-development domains, use standard validation
    try:
        result = _validate_email(
            email,
            check_deliverability=False,  # Skip DNS checks for development
            allow_smtputf8=True,
        )
        # Use normalized attribute to avoid deprecation warning
        return getattr(result, "normalized", result.email)
    except EmailNotValidError as e:
        raise ValueError(str(e))


class DevelopmentEmailStr(str):
    """
    A custom email type that allows development domains like .local, .localhost, .test.

    Use this instead of Pydantic's EmailStr when you need to support local/demo environments.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema

        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        """
        Generate JSON Schema for OpenAPI documentation.
        This makes the type appear as a string with email format in OpenAPI docs.
        """
        return {
            "type": "string",
            "format": "email",
            "description": "Email address (allows .local, .localhost, .test domains for development)",
        }

    @classmethod
    def _validate(cls, value, _info):
        return validate_email_with_local_domains(value)
