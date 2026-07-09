"""
Logs Router

Provides access to application runtime logs.
Admin-only access required.
Logs are stored in-memory and rotated automatically.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.admin import get_current_admin
from ..database import get_db
from ..logger.storage import add_log_to_storage, get_log_storage, get_storage_handler
from ..models import User
from ..schemas.common import ApiResponse

router = APIRouter(prefix="/logs", tags=["logs"])


class LogEntry(BaseModel):
    level: str
    args: list[Any]
    timestamp: datetime
    url: str | None = None
    message: str | None = None


class LogsPayload(BaseModel):
    logs: list[LogEntry]


class LogFilter(BaseModel):
    level: str | None = None
    limit: int = 100


@router.post("/client", response_model=ApiResponse[dict])
async def receive_client_logs(
    payload: LogsPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Receive console logs from the frontend client.
    Logs are stored per-user for debugging purposes.
    """
    log_count = len(payload.logs)

    # Store logs and log to server console
    storage = get_log_storage()
    for log in payload.logs:
        # Add to in-memory storage
        add_log_to_storage(
            log.level,
            log.message or str(log.args) if log.args else "",
            source="client",
            user_id=str(current_user.id),
            url=log.url
        )

        # Log to server console for immediate visibility
        if log.level == "error":
            print(f"[CLIENT ERROR] {log.timestamp}: {log.message or str(log.args)}")
        elif log.level == "warn":
            print(f"[CLIENT WARN] {log.timestamp}: {log.message or str(log.args)}")

    return ApiResponse(
        data={"received": log_count, "user_id": str(current_user.id)},
        message=f"Received {log_count} log entries",
    )


@router.get("/stats", response_model=ApiResponse[dict])
async def get_logs_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get statistics about recent logs.
    """
    storage = get_log_storage()
    stats = storage.get_stats()

    return ApiResponse(
        data={
            "user_id": str(current_user.id),
            **stats
        },
        message="Log statistics",
    )


@router.get("/entries", response_model=ApiResponse[dict])
async def get_log_entries(
    level: str | None = Query(None, description="Filter by log level (info, error, warning, debug, critical)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of entries to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get application runtime logs.
    Returns paginated log entries with optional level filtering.
    """
    storage = get_log_storage()
    logs = storage.get_logs(level=level, limit=limit)

    return ApiResponse(
        data={
            "logs": logs,
            "count": len(logs),
            "level_filter": level,
            "limit": limit
        },
        message=f"Retrieved {len(logs)} log entries",
    )


@router.post("/clear", response_model=ApiResponse[dict])
async def clear_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Clear all stored log entries.
    This action cannot be undone.
    """
    storage = get_log_storage()
    storage.clear()

    add_log_to_storage("info", "Logs cleared by user", user_id=str(current_user.id))

    return ApiResponse(
        data={"cleared": True},
        message="All logs have been cleared",
    )


@router.get("/levels", response_model=ApiResponse[list])
async def get_log_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get available log levels for filtering.
    """
    return ApiResponse(
        data=["info", "warning", "error", "debug", "critical"],
        message="Available log levels",
    )
