from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import EmotionAnalysis, Entry, User
from ..schemas.common import ApiResponse
from ..schemas.entries import AnalysisRead, EntryCreate, EntryRead
from ..services.analysis_service import analyze_text, analyze_text_with_llm
from ..utils.emotions import normalize_emotion_label

router = APIRouter(prefix="/entries", tags=["entries"])


def _get_conversation_messages(db: Session, conversation_id: int, user_id: int) -> list[dict] | None:
    """获取对话的消息用于情绪分析上下文。

    Args:
        db: 数据库会话
        conversation_id: 对话 ID
        user_id: 用户 ID

    Returns:
        消息列表 [{role, content}, ...] 或 None（如果对话不存在或不属于该用户）
    """
    try:
        from ..models.chat import Conversation, Message

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .first()
        )

        if not conversation:
            return None

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        return [{"role": msg.role, "content": msg.content} for msg in messages if msg.role in ("user", "assistant")]

    except Exception:
        # 如果出现任何错误，返回 None（不影响主流程）
        return None


def to_analysis_read(analysis: EmotionAnalysis) -> AnalysisRead:
    return AnalysisRead(
        id=analysis.id,
        primary_emotion=normalize_emotion_label(analysis.primary_emotion),
        secondary_emotions=[
            normalize_emotion_label(emotion)
            for emotion in json.loads(analysis.secondary_emotions or "[]")
        ],
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

    # 获取对话上下文（如果有）
    conversation_messages = None
    if payload.conversation_id:
        conversation_messages = _get_conversation_messages(db, payload.conversation_id, user.id)

    # 使用 LLM 进行情绪分析（支持对话上下文）
    result = analyze_text_with_llm(
        raw_content=payload.raw_content,
        conversation_messages=conversation_messages,
        db=db,
    )

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
            draft_title=result.get("title", "今天的心情记录"),
            draft_content=result.get("diary_content", f"今天我记录下了这段感受：{payload.raw_content}"),
        ),
        message="entry_analyzed",
    )
