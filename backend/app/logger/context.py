"""
Request context management for logging.

Provides request ID generation and propagation across async boundaries.
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Context variables for request-scoped data
_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id_ctx: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


def generate_request_id() -> str:
    """Generate a unique request ID.

    Uses UUID v4 for simplicity. For time-sortable IDs, consider UUID v7.

    Returns:
        A unique request ID string
    """
    return str(uuid.uuid4())


def get_request_id() -> Optional[str]:
    """Get the current request ID from context.

    Returns:
        The current request ID, or None if not set
    """
    return _request_id_ctx.get(None)


def get_user_id() -> Optional[int]:
    """Get the current user ID from context.

    Returns:
        The current user ID, or None if not set
    """
    return _user_id_ctx.get(None)


def set_request_context(request_id: str, user_id: Optional[int] = None) -> None:
    """Set request context data.

    Args:
        request_id: The request ID for this request
        user_id: Optional user ID for authenticated requests
    """
    _request_id_ctx.set(request_id)
    if user_id is not None:
        _user_id_ctx.set(user_id)


def clear_request_context() -> None:
    """Clear request context data at the end of a request."""
    _request_id_ctx.set(None)
    _user_id_ctx.set(None)
