from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntryCreate(BaseModel):
    raw_content: str = Field(min_length=1)
    input_type: str = "text"
    source_language: str = "zh-CN"


class AnalysisRead(BaseModel):
    id: int
    primary_emotion: str
    secondary_emotions: list[str]
    emotion_score: int
    valence: float
    arousal: float
    intensity: float
    risk_level: str
    risk_reason: Optional[str]
    summary: str
    suggestion: str


class EntryRead(BaseModel):
    id: int
    input_type: str
    raw_content: str
    source_language: str
    status: str
    created_at: datetime
    analysis: AnalysisRead
    draft_title: str
    draft_content: str
