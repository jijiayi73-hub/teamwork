from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..models import Conversation, Diary, Entry, MemoryCard, User
from ..schemas.auth import UserRead, UserUpdate
from ..schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def utc_now():
    return datetime.now(timezone.utc)


@router.get("/users", response_model=ApiResponse[list[UserRead]])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return ApiResponse(data=users)


@router.get("/users/{user_id}", response_model=ApiResponse[UserRead])
def get_user(user_id: int, current_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(data=user)


@router.patch("/users/{user_id}", response_model=ApiResponse[UserRead])
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion or self-role-change
    if user.id == current_admin.id:
        if payload.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        if payload.role and payload.role != "admin":
            raise HTTPException(status_code=400, detail="Cannot remove your own admin role")

    # Update fields
    if payload.status is not None:
        user.status = payload.status
        user.updated_at = utc_now()
    if payload.role is not None:
        user.role = payload.role
        user.updated_at = utc_now()

    db.commit()
    db.refresh(user)
    return ApiResponse(data=user)


@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Soft delete by setting status
    user.status = "deleted"
    user.updated_at = utc_now()
    db.commit()

    return ApiResponse(data={"deleted": True, "user_id": user_id})


@router.get("/stats", response_model=ApiResponse[dict])
def admin_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    seven_days_ago = date.today() - timedelta(days=6)
    return ApiResponse(
        data={
            "total_users": db.query(User).count(),
            "total_entries": db.query(Entry).count(),
            "total_diaries": db.query(Diary).filter(Diary.deleted_at.is_(None)).count(),
            "total_memory_cards": db.query(MemoryCard).filter(MemoryCard.deleted_at.is_(None)).count(),
            "total_conversations": db.query(Conversation).filter(Conversation.deleted_at.is_(None)).count(),
            "new_diaries_last_7_days": db.query(Diary)
            .filter(Diary.deleted_at.is_(None), Diary.diary_date >= seven_days_ago)
            .count(),
            "new_memory_cards_last_7_days": db.query(MemoryCard)
            .filter(MemoryCard.deleted_at.is_(None), MemoryCard.created_at >= seven_days_ago)
            .count(),
        }
    )


@router.get("/stats/charts", response_model=ApiResponse[dict])
def admin_chart_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    from collections import Counter

    seven_days_ago = date.today() - timedelta(days=6)
    memories = db.query(MemoryCard).filter(MemoryCard.deleted_at.is_(None)).all()
    emotion_counts = Counter(memory.emotion_label for memory in memories)
    daily_new = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        daily_new.append(
            {
                "date": day.isoformat(),
                "count": sum(1 for memory in memories if memory.created_at.date() == day),
            }
        )
    return ApiResponse(
        data={
            "total_users": db.query(User).count(),
            "total_entries": db.query(Entry).count(),
            "total_diaries": db.query(Diary).filter(Diary.deleted_at.is_(None)).count(),
            "total_memory_cards": len(memories),
            "total_conversations": db.query(Conversation).filter(Conversation.deleted_at.is_(None)).count(),
            "new_diaries_last_7_days": db.query(Diary)
            .filter(Diary.deleted_at.is_(None), Diary.diary_date >= seven_days_ago)
            .count(),
            "new_memory_cards_last_7_days": sum(1 for memory in memories if memory.created_at.date() >= seven_days_ago),
            "emotion_distribution": [
                {"emotion": emotion, "count": count} for emotion, count in emotion_counts.items()
            ],
            "daily_new_memory_cards": daily_new,
            "service_status": {
                "api": "healthy",
                "database": "connected",
                "ai_configured": True,
            },
            "privacy_note": "Admin stats do not expose private diary body content.",
        }
    )
