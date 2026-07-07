from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    entries: Mapped[List["Entry"]] = relationship(back_populates="user")
    diaries: Mapped[List["Diary"]] = relationship(back_populates="user")


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    input_type: Mapped[str] = mapped_column(String(20), default="text")
    raw_content: Mapped[str] = mapped_column(Text)
    source_language: Mapped[str] = mapped_column(String(20), default="zh-CN")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    audio_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped[User] = relationship(back_populates="entries")
    analysis: Mapped["EmotionAnalysis"] = relationship(back_populates="entry", uselist=False)
    diary: Mapped["Diary"] = relationship(back_populates="entry", uselist=False)


class EmotionAnalysis(Base):
    __tablename__ = "emotion_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="local-rule")
    model_name: Mapped[str] = mapped_column(String(100), default="minimal-backend-loop")
    primary_emotion: Mapped[str] = mapped_column(String(30))
    secondary_emotions: Mapped[str] = mapped_column(Text, default="[]")
    emotion_score: Mapped[int] = mapped_column(Integer)
    valence: Mapped[float] = mapped_column()
    arousal: Mapped[float] = mapped_column()
    intensity: Mapped[float] = mapped_column()
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    risk_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)
    raw_response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    entry: Mapped[Entry] = relationship(back_populates="analysis")
    diary: Mapped["Diary"] = relationship(back_populates="analysis", uselist=False)


class Diary(Base):
    __tablename__ = "diaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"), unique=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("emotion_analyses.id"), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    diary_date: Mapped[date] = mapped_column(Date)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    visibility: Mapped[str] = mapped_column(String(20), default="private")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="diaries")
    entry: Mapped[Entry] = relationship(back_populates="diary")
    analysis: Mapped[EmotionAnalysis] = relationship(back_populates="diary")
