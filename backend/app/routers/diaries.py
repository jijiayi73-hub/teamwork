from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import Diary, Entry, User
from ..schemas.common import ApiResponse
from ..schemas.diaries import DiaryCreate, DiaryRead, DiaryUpdate
from .entries import to_analysis_read

router = APIRouter(prefix="/diaries", tags=["diaries"])


def to_diary_read(diary: Diary) -> DiaryRead:
    return DiaryRead(
        id=diary.id,
        entry_id=diary.entry_id,
        analysis_id=diary.analysis_id,
        title=diary.title,
        content=diary.content,
        diary_date=diary.diary_date,
        is_favorite=diary.is_favorite,
        visibility=diary.visibility,
        created_at=diary.created_at,
        updated_at=diary.updated_at,
        analysis=to_analysis_read(diary.analysis),
    )


@router.post("", response_model=ApiResponse[DiaryRead], status_code=201)
def create_diary(payload: DiaryCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(Entry).filter(Entry.id == payload.entry_id, Entry.user_id == user.id).first()
    if not entry or not entry.analysis:
        raise HTTPException(status_code=404, detail="Analyzed entry not found")
    if entry.diary and entry.diary.deleted_at is None:
        raise HTTPException(status_code=409, detail="Diary already exists for entry")
    diary = Diary(
        user_id=user.id,
        entry_id=entry.id,
        analysis_id=entry.analysis.id,
        title=payload.title,
        content=payload.content,
        diary_date=payload.diary_date,
        is_favorite=payload.is_favorite,
    )
    entry.status = "confirmed"
    db.add(diary)
    db.commit()
    db.refresh(diary)
    return ApiResponse(data=to_diary_read(diary), message="diary_created")


@router.get("", response_model=ApiResponse[list[DiaryRead]])
def list_diaries(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diaries = (
        db.query(Diary)
        .filter(Diary.user_id == user.id, Diary.deleted_at.is_(None))
        .order_by(Diary.diary_date.desc(), Diary.id.desc())
        .all()
    )
    return ApiResponse(data=[to_diary_read(diary) for diary in diaries])


@router.get("/{diary_id}", response_model=ApiResponse[DiaryRead])
def get_diary(diary_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diary = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == user.id, Diary.deleted_at.is_(None)).first()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    return ApiResponse(data=to_diary_read(diary))


@router.patch("/{diary_id}", response_model=ApiResponse[DiaryRead])
def update_diary(diary_id: int, payload: DiaryUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diary = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == user.id, Diary.deleted_at.is_(None)).first()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(diary, field, value)
    db.commit()
    db.refresh(diary)
    return ApiResponse(data=to_diary_read(diary), message="diary_updated")


@router.delete("/{diary_id}", response_model=ApiResponse[dict])
def delete_diary(diary_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diary = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == user.id, Diary.deleted_at.is_(None)).first()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    diary.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return ApiResponse(data={"id": diary_id}, message="diary_deleted")
