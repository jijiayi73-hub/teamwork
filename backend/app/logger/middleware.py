"""
Request logging middleware for InnerGarden API.

Logs HTTP requests with timing, status codes, and request IDs.
Sensitive data is sanitized before logging.
"""

import time
from typing import Callable
from urllib.parse import parse_qs

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .context import clear_request_context, generate_request_id, set_request_context


# Sensitive keys that should never be logged
SENSITIVE_KEYS = {
    "password", "token", "secret", "key", "authorization",
    "access_token", "refresh_token", "api_key", "auth_token",
}


def sanitize_dict(data: dict, sensitive_keys: set[str] = None) -> dict:
    """Recursively sanitize sensitive data in dictionaries."""
    if sensitive_keys is None:
        sensitive_keys = SENSITIVE_KEYS

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, sensitive_keys)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log with timing information."""
        # Generate request ID and set context
        request_id = generate_request_id()
        set_request_context(request_id)

        # Get start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log successful request
            self._log_request(request, response, duration_ms, True)

            # Add request ID to response header
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log failed request
            self._log_request(request, None, duration_ms, False, str(e))

            # Re-raise for exception handler to process
            raise

        finally:
            # Clear context at end of request
            clear_request_context()

    def _log_request(
        self,
        request: Request,
        response: Response | None,
        duration_ms: float,
        success: bool,
        error: str = None
    ) -> None:
        """Log request information with sensitive data sanitized."""
        from .config import get_logger

        logger = get_logger("http.request")

        # Sanitize query params to remove sensitive data
        query_params = sanitize_dict(dict(request.query_params))

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": query_params,
            "client_ip": self._get_client_ip(request),
            "duration_ms": round(duration_ms, 2),
        }

        if response:
            log_data["status_code"] = response.status_code

        if error:
            log_data["error"] = error

        if success:
            logger.info("HTTP request completed", **log_data)
        else:
            logger.error("HTTP request failed", **log_data)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request, accounting for proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"
