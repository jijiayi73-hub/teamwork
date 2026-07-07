from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.diary import Diary


def get_diary(db: Session, diary_id: str) -> Diary | None:
    return db.get(Diary, diary_id)


def get_diary_by_conversation(db: Session, conversation_id: str) -> Diary | None:
    statement = select(Diary).where(Diary.conversation_id == conversation_id)
    return db.scalars(statement).first()


def save_diary(db: Session, diary: Diary) -> Diary:
    db.add(diary)
    db.commit()
    db.refresh(diary)
    return diary


def list_diaries(db: Session, page: int = 1, page_size: int = 20) -> list[Diary]:
    offset = (page - 1) * page_size
    statement = select(Diary).order_by(Diary.created_at.desc()).limit(page_size).offset(offset)
    return list(db.scalars(statement).all())
