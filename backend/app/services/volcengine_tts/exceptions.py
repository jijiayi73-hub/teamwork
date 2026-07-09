"""
Volcengine TTS Exceptions

TTS功能专用异常类定义。
"""


class VolcengineTTSError(Exception):
    """Base exception for Volcengine TTS errors."""

    def __init__(self, message: str, error_code: int = None, details: str = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ConnectionError(VolcengineTTSError):
    """WebSocket connection failed."""
    pass


class AuthenticationError(VolcengineTTSError):
    """Authentication failed."""
    pass


class SessionError(VolcengineTTSError):
    """Session creation or management failed."""
    pass


class ProtocolError(VolcengineTTSError):
    """Protocol frame encoding/parsing failed."""
    pass


class TimeoutError(VolcengineTTSError):
    """Operation timed out."""
    pass


class RateLimitError(VolcengineTTSError):
    """Rate limit exceeded."""
    pass


class ServerError(VolcengineTTSError):
    """Server-side error."""
    pass


# Common error codes from Volcengine TTS API
# Reference: https://www.volcengine.com/docs/6561/79817

ERROR_CODES = {
    20000000: "Success",
    45000000: "Client error",
    45000001: "Invalid request parameters",
    45000002: "Authentication failed",
    45000003: "Rate limit exceeded",
    45000004: "Invalid session ID",
    45000005: "Session already active",
    45000006: "Session not found",
    45000007: "Connection timeout",
    55000000: "Server error",
    55000001: "Server session error",
    55000002: "Server internal error",
    55000003: "Service unavailable",
}


def get_error_message(error_code: int) -> str:
    """Get human-readable error message from error code."""
    return ERROR_CODES.get(error_code, f"Unknown error code: {error_code}")
