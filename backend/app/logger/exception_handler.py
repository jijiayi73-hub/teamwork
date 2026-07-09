"""
Global exception handlers for InnerGarden API.

Provides secure error responses with comprehensive server-side logging.
"""

import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from ..schemas.common import ErrorCode, ErrorResponse
from .config import get_logger
from .context import get_request_id


logger = get_logger(__name__)


def add_exception_handlers(app: FastAPI) -> None:
    """Add all global exception handlers to the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
        """Handle HTTP exceptions with logging."""
        request_id = get_request_id() or "unknown"

        # Log the exception with full details server-side
        logger.warning(
            "HTTP exception",
            request_id=request_id,
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )

        # Store in in-memory log storage
        from .storage import add_log_to_storage
        add_log_to_storage(
            "warning",
            f"HTTP {exc.status_code}: {exc.detail}",
            request_id=request_id,
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method,
        )

        # Map status codes to error codes
        error_code = _map_status_to_error_code(exc.status_code)

        # Return secure response without exposing internal details
        error_response = ErrorResponse(
            success=False,
            data=None,
            message=exc.detail,
            request_id=request_id,
            error_code=error_code,
            details=None
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=exc.status_code
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> Response:
        """Handle Pydantic validation errors."""
        request_id = get_request_id() or "unknown"

        # Log validation errors
        logger.warning(
            "Validation error",
            request_id=request_id,
            errors=exc.errors(),
            path=request.url.path,
            method=request.method,
        )

        # Format error details for client
        details = {"fields": []}
        for error in exc.errors():
            details["fields"].append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        error_response = ErrorResponse(
            success=False,
            data=None,
            message="Validation failed",
            request_id=request_id,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError) -> Response:
        """Handle database integrity errors."""
        request_id = get_request_id() or "unknown"

        # Log database errors with full traceback
        logger.error(
            "Database integrity error",
            request_id=request_id,
            error=str(exc),
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
        )

        # Return generic error to client
        error_response = ErrorResponse(
            success=False,
            data=None,
            message="Data conflict. The resource may already exist.",
            request_id=request_id,
            error_code=ErrorCode.CONFLICT,
            details=None
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=status.HTTP_409_CONFLICT
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> Response:
        """Handle all other exceptions with logging."""
        request_id = get_request_id() or "unknown"

        # Log with full traceback for debugging
        logger.error(
            "Unhandled exception",
            request_id=request_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
        )

        # Store in in-memory log storage
        from .storage import add_log_to_storage
        add_log_to_storage(
            "error",
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            request_id=request_id,
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
        )

        # Return generic error to client - never expose internal details
        error_response = ErrorResponse(
            success=False,
            data=None,
            message="An internal error occurred. Please contact support with your request ID.",
            request_id=request_id,
            error_code=ErrorCode.INTERNAL_ERROR,
            details=None
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _map_status_to_error_code(status_code: int) -> ErrorCode:
    """Map HTTP status codes to error codes."""
    mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)
