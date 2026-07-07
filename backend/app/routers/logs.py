"""
Logs Router

Handles frontend console logs for debugging.
In production, logs should be sent to a proper logging service.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
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


@router.post("/client", response_model=ApiResponse[dict])
async def receive_client_logs(
    payload: LogsPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receive console logs from the frontend client.
    Logs are stored per-user for debugging purposes.
    """
    # In a real application, you would:
    # 1. Store logs in a separate logs table
    # 2. Implement log rotation/cleanup
    # 3. Use a proper logging service like Sentry, LogRocket, etc.

    # For now, we'll just acknowledge receipt
    # You can extend this to store logs in the database or send to an external service

    log_count = len(payload.logs)

    # Log to server console for immediate visibility
    for log in payload.logs:
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
    current_user: User = Depends(get_current_user),
):
    """
    Get statistics about recent logs (placeholder).
    """
    return ApiResponse(
        data={
            "user_id": str(current_user.id),
            "message": "Log statistics not yet implemented",
        },
        message="Log stats",
    )
