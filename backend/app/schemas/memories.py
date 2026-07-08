from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from .entries import AnalysisRead


class MemoryCardCreate(BaseModel):
    diary_id: int
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    cover_prompt: Optional[str] = None
    emotion_label: str = Field(default="calm", min_length=1, max_length=30)
    emotion_color: str = Field(default="#8fb8ff", min_length=1, max_length=40)
    keywords: list[str] = Field(default_factory=list)
    conversation_summary: Optional[str] = None


class MemoryCardUpdate(BaseModel):
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    cover_prompt: Optional[str] = None
    emotion_label: Optional[str] = Field(default=None, min_length=1, max_length=30)
    emotion_color: Optional[str] = Field(default=None, min_length=1, max_length=40)
    keywords: Optional[list[str]] = None
    conversation_summary: Optional[str] = None


class DiarySnapshot(BaseModel):
    id: int
    title: str
    content: str
    diary_date: date
    created_at: datetime
    updated_at: datetime
    analysis: AnalysisRead


class MemoryCardRead(BaseModel):
    id: int
    diary_id: int
    title: str
    excerpt: str
    diary_date: date
    cover_image_url: Optional[str]
    cover_prompt: Optional[str]
    emotion_label: str
    emotion_color: str
    keywords: list[str]
    conversation_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    diary: DiarySnapshot


class PastSelfChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: Optional[int] = None


class UploadedAssetRead(BaseModel):
    id: int
    url: str
    original_filename: str
    content_type: str
    created_at: datetime


class ImageUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    data_url: str = Field(min_length=1)
