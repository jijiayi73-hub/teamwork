from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import EmotionAnalysis, Entry, User
from ..schemas.common import ApiResponse
from ..schemas.entries import AnalysisRead, EntryCreate, EntryRead
from ..services.analysis_service import analyze_text

router = APIRouter(prefix="/entries", tags=["entries"])


def to_analysis_read(analysis: EmotionAnalysis) -> AnalysisRead:
    return AnalysisRead(
        id=analysis.id,
        primary_emotion=analysis.primary_emotion,
        secondary_emotions=json.loads(analysis.secondary_emotions or "[]"),
        emotion_score=analysis.emotion_score,
        valence=analysis.valence,
        arousal=analysis.arousal,
        intensity=analysis.intensity,
        risk_level=analysis.risk_level,
        risk_reason=analysis.risk_reason,
        summary=analysis.summary,
        suggestion=analysis.suggestion,
    )


@router.post("", response_model=ApiResponse[EntryRead], status_code=201)
def create_entry(payload: EntryCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.input_type != "text":
        raise HTTPException(status_code=400, detail="Minimal backend loop supports text entries first")
    entry = Entry(
        user_id=user.id,
        input_type=payload.input_type,
        raw_content=payload.raw_content,
        source_language=payload.source_language,
        status="analyzed",
    )
    db.add(entry)
    db.flush()
    result = analyze_text(payload.raw_content)
    analysis = EmotionAnalysis(
        entry_id=entry.id,
        primary_emotion=result["primary_emotion"],
        secondary_emotions=json.dumps(result["secondary_emotions"], ensure_ascii=False),
        emotion_score=result["emotion_score"],
        valence=result["valence"],
        arousal=result["arousal"],
        intensity=result["intensity"],
        risk_level=result["risk_level"],
        risk_reason=result["risk_reason"],
        summary=result["summary"],
        suggestion=result["suggestion"],
        raw_response_json=result["raw_response_json"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(entry)
    db.refresh(analysis)
    return ApiResponse(
        data=EntryRead(
            id=entry.id,
            input_type=entry.input_type,
            raw_content=entry.raw_content,
            source_language=entry.source_language,
            status=entry.status,
            created_at=entry.created_at,
            analysis=to_analysis_read(analysis),
            draft_title=result["title"],
            draft_content=result["diary_content"],
        ),
        message="entry_analyzed",
    )
