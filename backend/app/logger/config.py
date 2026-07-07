"""
Logging configuration for InnerGarden API.

Provides structured logging with environment-aware configuration.
"""

import logging
import sys
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

from ..config import settings


# Processor to add request context to all logs
def add_request_context(logger, method_name, event_dict) -> dict:
    """Add request context (request_id, user_id) to log entries."""
    from .context import get_request_id, get_user_id

    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id

    user_id = get_user_id()
    if user_id is not None:
        event_dict["user_id"] = user_id

    return event_dict


def configure_logging() -> None:
    """Configure structlog with appropriate processors for the environment."""

    # Configure standard logging for structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    if settings.app_env == "production":
        _configure_production()
    else:
        _configure_development()


def _configure_production() -> None:
    """Configure JSON logging for production."""

    def add_app_context(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
        """Add application-level context to log entries."""
        event_dict["app"] = "innergarden"
        event_dict["environment"] = settings.app_env
        return event_dict

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_request_context,
            add_app_context,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _configure_development() -> None:
    """Configure console logging for development."""

    # Custom processor to add colors based on log level
    def add_level_colors(logger, method_name, event_dict):
        level = event_dict.get("level", "info").upper()
        level_colors = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m", # Magenta
        }
        reset = "\033[0m"
        color = level_colors.get(level, "")
        if color:
            event_dict["level"] = f"{color}{level}{reset}"
        return event_dict

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_request_context,
            add_level_colors,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a context-aware logger instance.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        A bound logger instance
    """
    return structlog.get_logger(name)
