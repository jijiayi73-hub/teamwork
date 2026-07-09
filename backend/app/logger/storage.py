"""
In-memory log storage for InnerGarden API.

Stores log entries in memory with automatic rotation.
"""

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

from .config import get_logger

logger = get_logger(__name__)


# Log entry structure
class LogEntry:
    """A single log entry."""

    def __init__(self, level: str, message: str, timestamp: datetime = None, **extra):
        self.level = level.upper()
        self.message = message
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            **self.extra
        }


class LogStorage:
    """Thread-safe in-memory log storage with automatic rotation."""

    def __init__(self, max_entries: int = 1000):
        """
        Initialize log storage.

        Args:
            max_entries: Maximum number of log entries to keep
        """
        self.max_entries = max_entries
        self._logs = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def add(self, level: str, message: str, **extra) -> None:
        """Add a log entry."""
        entry = LogEntry(level, message, **extra)
        with self._lock:
            self._logs.append(entry)

    def get_logs(self, level: str = None, limit: int = 100) -> list[dict]:
        """
        Retrieve log entries.

        Args:
            level: Filter by log level (info, error, warning, etc.)
            limit: Maximum number of entries to return

        Returns:
            List of log entry dictionaries
        """
        with self._lock:
            logs = list(self._logs)

        if level:
            level_upper = level.upper()
            logs = [log for log in logs if log.level == level_upper]

        # Return most recent logs first
        logs.reverse()
        return [log.to_dict() for log in logs[:limit]]

    def get_stats(self) -> dict[str, int]:
        """Get log statistics."""
        with self._lock:
            logs = list(self._logs)

        stats = {
            "total": len(logs),
            "info": 0,
            "warning": 0,
            "error": 0,
            "debug": 0,
            "critical": 0
        }

        for log in logs:
            level_lower = log.level.lower()
            if level_lower in stats:
                stats[level_lower] += 1

        return stats

    def clear(self) -> None:
        """Clear all log entries."""
        with self._lock:
            self._logs.clear()


# Global log storage instance
_log_storage = LogStorage(max_entries=2000)


def get_log_storage() -> LogStorage:
    """Get the global log storage instance."""
    return _log_storage


class StorageHandler:
    """Custom logging handler that stores logs in memory."""

    def __init__(self, storage: LogStorage):
        self.storage = storage

    def emit(self, level: str, message: str, **kwargs) -> None:
        """Emit a log entry to storage."""
        try:
            # Extract relevant context from kwargs
            extra = {}
            if "request_id" in kwargs:
                extra["request_id"] = kwargs["request_id"]
            if "user_id" in kwargs:
                extra["user_id"] = kwargs["user_id"]
            if "path" in kwargs:
                extra["path"] = kwargs["path"]
            if "method" in kwargs:
                extra["method"] = kwargs["method"]
            if "status_code" in kwargs:
                extra["status_code"] = kwargs["status_code"]
            if "duration_ms" in kwargs:
                extra["duration_ms"] = kwargs["duration_ms"]

            self.storage.add(level, message, **extra)
        except Exception as e:
            # Don't raise exceptions in logging handler
            logger.error("Failed to store log entry", error=str(e))


# Global storage handler instance
_storage_handler = None


def get_storage_handler() -> StorageHandler:
    """Get the global storage handler instance."""
    global _storage_handler
    if _storage_handler is None:
        _storage_handler = StorageHandler(_log_storage)
    return _storage_handler


def add_log_to_storage(level: str, message: str, **extra) -> None:
    """
    Add a log entry to storage.

    This is a convenience function that can be called directly
    without going through the logging system.

    Args:
        level: Log level (info, error, warning, etc.)
        message: Log message
        **extra: Additional context data
    """
    _log_storage.add(level, message, **extra)
