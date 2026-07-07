"""
Timing decorators for database and LLM operations.

Logs timing information for performance monitoring.
"""

import functools
import time
from typing import Callable

from ..logger.config import get_logger


def timed_db_operation(operation_name: str = None):
    """Decorator to time database operations.

    Args:
        operation_name: Optional name for the operation (defaults to function name)

    Usage:
        @timed_db_operation("create_user")
        def create_user(db, user_data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("db.operation")
            op_name = operation_name or func.__name__
            start_time = time.time()
            success = False
            result = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "Database operation completed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=success,
                )

        return wrapper
    return decorator


def timed_llm_call(operation_name: str = None):
    """Decorator to time LLM or analysis service calls.

    Args:
        operation_name: Optional name for the operation (defaults to function name)

    Usage:
        @timed_llm_call("analyze_emotion")
        def analyze_text(raw_content):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("llm.call")
            op_name = operation_name or func.__name__
            start_time = time.time()
            success = False
            result = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "LLM/Analysis call completed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=success,
                )

        return wrapper
    return decorator


def timed_api_call(operation_name: str = None):
    """Decorator to time external API calls.

    Args:
        operation_name: Optional name for the operation (defaults to function name)

    Usage:
        @timed_api_call("openai_completion")
        def call_openai_api(prompt):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("api.call")
            op_name = operation_name or func.__name__
            start_time = time.time()
            success = False
            result = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                logger.error(
                    "External API call failed",
                    operation=op_name,
                    error=str(e),
                )
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "External API call completed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=success,
                )

        return wrapper
    return decorator
