from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from .entries import AnalysisRead


class DiaryCreate(BaseModel):
    entry_id: int
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    diary_date: date
    is_favorite: bool = False


class DiaryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    content: Optional[str] = Field(default=None, min_length=1)
    diary_date: Optional[date] = None
    is_favorite: Optional[bool] = None


class DiaryRead(BaseModel):
    id: int
    entry_id: int
    analysis_id: int
    title: str
    content: str
    diary_date: date
    is_favorite: bool
    visibility: str
    created_at: datetime
    updated_at: datetime
    analysis: AnalysisRead
