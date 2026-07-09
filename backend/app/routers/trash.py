"""Trash/recycle bin router for Inner Garden.

This module provides endpoints for managing deleted Memory Cards and Diaries:
- List deleted items
- Restore deleted items
- Permanently delete items
- Batch operations
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import Diary, User
from ..models.chat import Conversation
from ..models.diary import MemoryCard
from ..schemas.common import ApiResponse
from ..schemas.trash import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchRestoreRequest,
    BatchRestoreResponse,
    EmptyTrashResponse,
    RestoreResponse,
    TrashItemRead,
    TrashListResponse,
)
from ..utils.emotions import normalize_emotion_label

router = APIRouter(prefix="/trash", tags=["trash"])


def _to_trash_item(memory: MemoryCard, deleted_conv_count: int) -> TrashItemRead:
    """Convert a deleted MemoryCard to TrashItemRead."""
    diary = memory.diary
    return TrashItemRead(
        id=memory.id,
        diary_id=diary.id if diary else memory.diary_id,
        title=diary.title if diary else "Unknown",
        excerpt=diary.content[:180] if diary else "",
        diary_date=diary.diary_date.isoformat() if diary else "",
        cover_image_url=memory.cover_image_url,
        emotion_label=normalize_emotion_label(memory.emotion_label),
        emotion_color=memory.emotion_color,
        deleted_at=memory.deleted_at or datetime.now(timezone.utc),
        deleted_conversations_count=deleted_conv_count,
    )


def _count_deleted_conversations(db: Session, user_id: int, diary_id: int) -> int:
    """Count deleted conversations for a specific diary."""
    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.anchor_diary_id == diary_id,
            Conversation.deleted_at.isnot(None),
        )
        .count()
    )


# ============================================================================
# Batch operations - MUST be defined before single item operations
# ============================================================================


@router.post("/batch/restore", response_model=ApiResponse[BatchRestoreResponse])
def batch_restore(
    payload: BatchRestoreRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restore multiple deleted Memory Cards at once.

    Attempts to restore all specified items, continuing even if some fail.
    """
    restored_count = 0
    skipped_count = 0
    errors = []

    for memory_id in payload.memory_ids:
        try:
            # Find the deleted memory card
            memory = (
                db.query(MemoryCard)
                .filter(
                    MemoryCard.id == memory_id,
                    MemoryCard.user_id == user.id,
                    MemoryCard.deleted_at.isnot(None),
                )
                .first()
            )

            if not memory:
                skipped_count += 1
                continue

            diary_id = memory.diary_id

            # Restore associated conversations
            restored_conversations = (
                db.query(Conversation)
                .filter(
                    Conversation.user_id == user.id,
                    Conversation.anchor_diary_id == diary_id,
                    Conversation.deleted_at.isnot(None),
                )
                .all()
            )

            for conv in restored_conversations:
                conv.deleted_at = None

            # Restore the diary
            diary = (
                db.query(Diary)
                .filter(
                    Diary.id == diary_id,
                    Diary.user_id == user.id,
                    Diary.deleted_at.isnot(None),
                )
                .first()
            )

            if diary:
                diary.deleted_at = None

            # Restore the memory card
            memory.deleted_at = None
            restored_count += 1

        except Exception as e:
            errors.append(f"Memory {memory_id}: {str(e)}")

    db.commit()

    return ApiResponse(
        data=BatchRestoreResponse(
            restored_count=restored_count,
            skipped_count=skipped_count,
            errors=errors,
        ),
        message="batch_restore_completed",
    )


@router.delete("/batch", response_model=ApiResponse[BatchDeleteResponse])
def batch_permanent_delete(
    payload: BatchDeleteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete multiple Memory Cards at once.

    WARNING: This action cannot be undone.
    """
    deleted_count = 0
    skipped_count = 0

    for memory_id in payload.memory_ids:
        # Find the deleted memory card
        memory = (
            db.query(MemoryCard)
            .filter(
                MemoryCard.id == memory_id,
                MemoryCard.user_id == user.id,
                MemoryCard.deleted_at.isnot(None),
            )
            .first()
        )

        if not memory:
            skipped_count += 1
            continue

        diary_id = memory.diary_id

        # Delete associated conversations permanently
        deleted_conversations = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user.id,
                Conversation.anchor_diary_id == diary_id,
                Conversation.deleted_at.isnot(None),
            )
            .all()
        )

        for conv in deleted_conversations:
            db.delete(conv)

        # Delete the diary permanently
        diary = (
            db.query(Diary)
            .filter(
                Diary.id == diary_id,
                Diary.user_id == user.id,
                Diary.deleted_at.isnot(None),
            )
            .first()
        )

        if diary:
            db.delete(diary)

        # Delete the memory card permanently
        db.delete(memory)
        deleted_count += 1

    db.commit()

    return ApiResponse(
        data=BatchDeleteResponse(
            deleted_count=deleted_count,
            skipped_count=skipped_count,
        ),
        message="batch_permanent_delete_completed",
    )


@router.delete("/all", response_model=ApiResponse[EmptyTrashResponse])
def empty_trash(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete all items in the trash.

    WARNING: This action cannot be undone.
    """
    # Get all deleted memory cards for the user
    deleted_memories = (
        db.query(MemoryCard)
        .filter(MemoryCard.user_id == user.id, MemoryCard.deleted_at.isnot(None))
        .all()
    )

    deleted_count = len(deleted_memories)

    for memory in deleted_memories:
        diary_id = memory.diary_id

        # Delete associated conversations permanently
        deleted_conversations = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user.id,
                Conversation.anchor_diary_id == diary_id,
                Conversation.deleted_at.isnot(None),
            )
            .all()
        )

        for conv in deleted_conversations:
            db.delete(conv)

        # Delete the diary permanently
        diary = (
            db.query(Diary)
            .filter(
                Diary.id == diary_id,
                Diary.user_id == user.id,
                Diary.deleted_at.isnot(None),
            )
            .first()
        )

        if diary:
            db.delete(diary)

        # Delete the memory card permanently
        db.delete(memory)

    db.commit()

    return ApiResponse(
        data=EmptyTrashResponse(deleted_count=deleted_count),
        message="trash_emptied",
    )


# ============================================================================
# Single item operations
# ============================================================================


@router.get("", response_model=ApiResponse[TrashListResponse])
def list_trash(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all deleted Memory Cards in the trash.

    Returns deleted items sorted by deletion time (most recent first).
    Includes count of associated conversations that were also deleted.
    """
    # Get all deleted memory cards for the user
    deleted_memories = (
        db.query(MemoryCard)
        .filter(MemoryCard.user_id == user.id, MemoryCard.deleted_at.isnot(None))
        .order_by(MemoryCard.deleted_at.desc(), MemoryCard.id.desc())
        .all()
    )

    # Convert to trash items with conversation counts
    items = []
    for memory in deleted_memories:
        conv_count = _count_deleted_conversations(db, user.id, memory.diary_id)
        items.append(_to_trash_item(memory, conv_count))

    return ApiResponse(
        data=TrashListResponse(items=items, total=len(items)),
        message="trash_listed",
    )


@router.post("/{memory_id}/restore", response_model=ApiResponse[RestoreResponse])
def restore_item(
    memory_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restore a deleted Memory Card and its associated Diary.

    Also restores any Past Self conversations that were deleted with it.
    """
    # Find the deleted memory card
    memory = (
        db.query(MemoryCard)
        .filter(
            MemoryCard.id == memory_id,
            MemoryCard.user_id == user.id,
            MemoryCard.deleted_at.isnot(None),
        )
        .first()
    )

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deleted memory not found"
        )

    diary_id = memory.diary_id

    # Restore associated conversations
    restored_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.anchor_diary_id == diary_id,
            Conversation.deleted_at.isnot(None),
        )
        .all()
    )

    for conv in restored_conversations:
        conv.deleted_at = None

    # Restore the diary
    diary = (
        db.query(Diary)
        .filter(
            Diary.id == diary_id,
            Diary.user_id == user.id,
            Diary.deleted_at.isnot(None),
        )
        .first()
    )

    diary_restored = False
    if diary:
        diary.deleted_at = None
        diary_restored = True

    # Restore the memory card
    memory.deleted_at = None
    db.commit()

    return ApiResponse(
        data=RestoreResponse(
            id=memory_id,
            diary_restored=diary_restored,
            conversations_restored=len(restored_conversations),
        ),
        message="item_restored",
    )


@router.delete("/{memory_id}", response_model=ApiResponse[dict])
def permanent_delete_item(
    memory_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a Memory Card and its associated Diary.

    WARNING: This action cannot be undone.
    """
    # Find the deleted memory card
    memory = (
        db.query(MemoryCard)
        .filter(
            MemoryCard.id == memory_id,
            MemoryCard.user_id == user.id,
            MemoryCard.deleted_at.isnot(None),
        )
        .first()
    )

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deleted memory not found"
        )

    diary_id = memory.diary_id

    # Delete associated conversations permanently
    deleted_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.anchor_diary_id == diary_id,
            Conversation.deleted_at.isnot(None),
        )
        .all()
    )

    for conv in deleted_conversations:
        db.delete(conv)

    # Delete the diary permanently
    diary = (
        db.query(Diary)
        .filter(
            Diary.id == diary_id,
            Diary.user_id == user.id,
            Diary.deleted_at.isnot(None),
        )
        .first()
    )

    if diary:
        db.delete(diary)

    # Delete the memory card permanently
    db.delete(memory)
    db.commit()

    return ApiResponse(
        data={"id": memory_id, "diary_deleted": diary is not None},
        message="item_permanently_deleted",
    )
