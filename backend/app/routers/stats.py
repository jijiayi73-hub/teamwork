from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import Diary, User
from ..schemas.common import ApiResponse
from ..utils.emotions import normalize_emotion_label

router = APIRouter(prefix="/stats", tags=["stats"])


def user_diaries(db: Session, user_id: int) -> list[Diary]:
    return db.query(Diary).filter(Diary.user_id == user_id, Diary.deleted_at.is_(None)).all()


@router.get("/overview", response_model=ApiResponse[dict])
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diaries = user_diaries(db, user.id)
    scores = [diary.analysis.emotion_score for diary in diaries if diary.analysis]
    return ApiResponse(
        data={
            "total_diaries": len(diaries),
            "favorite_diaries": sum(diary.is_favorite for diary in diaries),
            "average_emotion_score": round(sum(scores) / len(scores), 2) if scores else None,
        }
    )


@router.get("/emotion-trend", response_model=ApiResponse[list[dict]])
def emotion_trend(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diaries = sorted(user_diaries(db, user.id), key=lambda item: item.diary_date)
    return ApiResponse(
        data=[
            {
                "date": diary.diary_date.isoformat(),
                "emotion_score": diary.analysis.emotion_score if diary.analysis else 0,
                "primary_emotion": normalize_emotion_label(diary.analysis.primary_emotion if diary.analysis else None),
            }
            for diary in diaries
        ]
    )


@router.get("/emotion-distribution", response_model=ApiResponse[list[dict]])
def emotion_distribution(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    counts = Counter(
        normalize_emotion_label(diary.analysis.primary_emotion)
        for diary in user_diaries(db, user.id)
        if diary.analysis
    )
    return ApiResponse(data=[{"primary_emotion": emotion, "count": count} for emotion, count in counts.items()])
