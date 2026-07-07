from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..models import Diary, Entry, User
from ..schemas.auth import UserRead
from ..schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=ApiResponse[list[UserRead]])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return ApiResponse(data=users)


@router.get("/stats", response_model=ApiResponse[dict])
def admin_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    seven_days_ago = date.today() - timedelta(days=6)
    return ApiResponse(
        data={
            "total_users": db.query(User).count(),
            "total_entries": db.query(Entry).count(),
            "total_diaries": db.query(Diary).filter(Diary.deleted_at.is_(None)).count(),
            "new_diaries_last_7_days": db.query(Diary)
            .filter(Diary.deleted_at.is_(None), Diary.diary_date >= seven_days_ago)
            .count(),
        }
    )
