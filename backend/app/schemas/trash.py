"""Trash/recycle bin schemas for Inner Garden.

This module defines schemas for the trash functionality, allowing users to
view and restore deleted Memory Cards and their associated Diaries.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrashItemRead(BaseModel):
    """A deleted item in the trash (Memory Card with associated Diary)."""

    id: int = Field(..., description="Memory Card ID")
    diary_id: int = Field(..., description="Associated Diary ID")
    title: str = Field(..., description="Diary title")
    excerpt: str = Field(..., description="Diary content excerpt")
    diary_date: str = Field(..., description="Diary date (ISO format)")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")
    emotion_label: str = Field(..., description="Primary emotion")
    emotion_color: str = Field(..., description="Emotion color hex code")
    deleted_at: datetime = Field(..., description="When this item was deleted")
    deleted_conversations_count: int = Field(
        ..., description="Number of conversations also deleted"
    )

    class Config:
        from_attributes = True


class TrashListResponse(BaseModel):
    """Response model for trash list endpoint."""

    items: list[TrashItemRead] = Field(
        ..., description="List of deleted items, sorted by deletion time"
    )
    total: int = Field(..., description="Total number of items in trash")


class RestoreResponse(BaseModel):
    """Response model for restore endpoint."""

    id: int = Field(..., description="Memory Card ID that was restored")
    diary_restored: bool = Field(..., description="Whether the Diary was also restored")
    conversations_restored: int = Field(
        ..., description="Number of conversations restored"
    )


class BatchRestoreRequest(BaseModel):
    """Request model for batch restore."""

    memory_ids: list[int] = Field(
        ..., min_length=1, description="List of Memory Card IDs to restore"
    )


class BatchRestoreResponse(BaseModel):
    """Response model for batch restore endpoint."""

    restored_count: int = Field(..., description="Number of items successfully restored")
    skipped_count: int = Field(..., description="Number of items skipped (not found)")
    errors: list[str] = Field(default_factory=list, description="Any error messages")


class BatchDeleteRequest(BaseModel):
    """Request model for batch permanent delete."""

    memory_ids: list[int] = Field(
        ..., min_length=1, description="List of Memory Card IDs to permanently delete"
    )


class BatchDeleteResponse(BaseModel):
    """Response model for batch permanent delete endpoint."""

    deleted_count: int = Field(..., description="Number of items permanently deleted")
    skipped_count: int = Field(..., description="Number of items skipped (not found)")


class EmptyTrashResponse(BaseModel):
    """Response model for empty trash endpoint."""

    deleted_count: int = Field(..., description="Number of items permanently deleted")
