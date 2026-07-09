from __future__ import annotations

import json
import base64
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import Diary, MemoryCard, UploadedAsset, User
from ..models.chat import Conversation
from ..schemas.chat import ChatRequest
from ..schemas.common import ApiResponse
from ..schemas.memories import (
    DiarySnapshot,
    ImageUploadRequest,
    MemoryCardCreate,
    MemoryCardRead,
    MemoryCardUpdate,
    PastSelfChatRequest,
    UploadedAssetRead,
)
from ..services.chat_service import ChatService
from ..utils.emotions import normalize_emotion_label
from .entries import to_analysis_read

router = APIRouter(tags=["memories"])

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "data" / "uploads"
PUBLIC_UPLOAD_PREFIX = "/uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_IMAGE_BYTES = 12 * 1024 * 1024


def _keywords_to_json(keywords: list[str]) -> str:
    cleaned = [item.strip() for item in keywords if item and item.strip()]
    return json.dumps(cleaned[:12], ensure_ascii=False)


def _keywords_from_json(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _memory_matches_keyword(memory: MemoryCard, keyword: str) -> bool:
    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        return True

    diary = memory.diary
    searchable_values = [
        normalize_emotion_label(memory.emotion_label),
        memory.emotion_label,
        memory.conversation_summary,
        memory.cover_prompt,
        diary.title if diary else "",
        diary.content if diary else "",
    ]
    searchable_values.extend(_keywords_from_json(memory.keywords_json))
    return any(keyword_lower in str(value).lower() for value in searchable_values if value)


def _default_cover_prompt(diary: Diary) -> str:
    emotion = normalize_emotion_label(diary.analysis.primary_emotion if diary.analysis else None, default="平静")
    return (
        f"Soft therapeutic watercolor memory card cover for a diary titled "
        f"{diary.title!r}, main emotion {emotion}, gentle garden light."
    )


def _to_memory_read(memory: MemoryCard) -> MemoryCardRead:
    diary = memory.diary
    return MemoryCardRead(
        id=memory.id,
        diary_id=memory.diary_id,
        title=diary.title,
        excerpt=diary.content[:180],
        diary_date=diary.diary_date,
        cover_image_url=memory.cover_image_url,
        cover_prompt=memory.cover_prompt,
        emotion_label=normalize_emotion_label(memory.emotion_label),
        emotion_color=memory.emotion_color,
        keywords=_keywords_from_json(memory.keywords_json),
        conversation_summary=memory.conversation_summary,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        diary=DiarySnapshot(
            id=diary.id,
            title=diary.title,
            content=diary.content,
            diary_date=diary.diary_date,
            created_at=diary.created_at,
            updated_at=diary.updated_at,
            analysis=to_analysis_read(diary.analysis),
        ),
    )


def _get_user_memory(db: Session, user_id: int, memory_id: int) -> MemoryCard | None:
    return (
        db.query(MemoryCard)
        .filter(
            MemoryCard.id == memory_id,
            MemoryCard.user_id == user_id,
            MemoryCard.deleted_at.is_(None),
        )
        .first()
    )


@router.post("/uploads/images", response_model=ApiResponse[UploadedAssetRead], status_code=status.HTTP_201_CREATED)
def upload_image(
    payload: ImageUploadRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, WebP, or GIF images are supported")

    suffix = Path(payload.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }[payload.content_type]

    data_part = payload.data_url
    if "," in data_part:
        data_part = data_part.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(data_part, validate=True)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid base64 image data")
    if len(image_bytes) > MAX_UPLOAD_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image upload limit is 12MB")

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{user.id}-{uuid4().hex}{suffix}"
    target = UPLOAD_ROOT / stored_filename
    with target.open("wb") as output:
        output.write(image_bytes)

    asset = UploadedAsset(
        user_id=user.id,
        original_filename=payload.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=payload.content_type,
        url=f"{PUBLIC_UPLOAD_PREFIX}/{stored_filename}",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return ApiResponse(
        data=UploadedAssetRead(
            id=asset.id,
            url=asset.url,
            original_filename=asset.original_filename,
            content_type=asset.content_type,
            created_at=asset.created_at,
        ),
        message="image_uploaded",
    )


@router.post("/memories", response_model=ApiResponse[MemoryCardRead], status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCardCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    diary = (
        db.query(Diary)
        .filter(Diary.id == payload.diary_id, Diary.user_id == user.id, Diary.deleted_at.is_(None))
        .first()
    )
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    if diary.memory_card and diary.memory_card.deleted_at is None:
        raise HTTPException(status_code=409, detail="Memory card already exists for diary")

    memory = MemoryCard(
        user_id=user.id,
        diary_id=diary.id,
        cover_image_url=payload.cover_image_url,
        cover_prompt=payload.cover_prompt or _default_cover_prompt(diary),
        emotion_label=normalize_emotion_label(payload.emotion_label),
        emotion_color=payload.emotion_color,
        keywords_json=_keywords_to_json(payload.keywords),
        conversation_summary=payload.conversation_summary,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return ApiResponse(data=_to_memory_read(memory), message="memory_created")


@router.get("/memories", response_model=ApiResponse[list[MemoryCardRead]])
def list_memories(
    emotion: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MemoryCard).filter(MemoryCard.user_id == user.id, MemoryCard.deleted_at.is_(None))
    memories = query.order_by(MemoryCard.created_at.desc(), MemoryCard.id.desc()).all()
    if emotion:
        target_emotion = normalize_emotion_label(emotion)
        memories = [
            memory for memory in memories
            if normalize_emotion_label(memory.emotion_label) == target_emotion
        ]
    if keyword:
        memories = [memory for memory in memories if _memory_matches_keyword(memory, keyword)]
    return ApiResponse(data=[_to_memory_read(memory) for memory in memories])


@router.get("/memories/{memory_id}", response_model=ApiResponse[MemoryCardRead])
def get_memory(memory_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")
    return ApiResponse(data=_to_memory_read(memory))


@router.patch("/memories/{memory_id}", response_model=ApiResponse[MemoryCardRead])
def update_memory(
    memory_id: int,
    payload: MemoryCardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")

    update = payload.model_dump(exclude_unset=True)
    if "keywords" in update:
        memory.keywords_json = _keywords_to_json(update.pop("keywords") or [])
    if "emotion_label" in update and update["emotion_label"] is not None:
        update["emotion_label"] = normalize_emotion_label(update["emotion_label"])
    for field, value in update.items():
        setattr(memory, field, value)
    db.commit()
    db.refresh(memory)
    return ApiResponse(data=_to_memory_read(memory), message="memory_updated")


@router.delete("/memories/{memory_id}", response_model=ApiResponse[dict])
def delete_memory(memory_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")

    # Get the diary ID before deleting memory
    diary_id = memory.diary_id

    # Delete all associated conversations (past_self chats anchored to this diary)
    associated_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.anchor_diary_id == diary_id,
            Conversation.deleted_at.is_(None),
        )
        .all()
    )

    now = datetime.now(timezone.utc)
    for conv in associated_conversations:
        conv.deleted_at = now

    # Soft delete the memory card
    memory.deleted_at = now

    # Also soft delete the associated diary
    diary = db.query(Diary).filter(
        Diary.id == diary_id,
        Diary.user_id == user.id,
        Diary.deleted_at.is_(None)
    ).first()
    if diary:
        diary.deleted_at = now

    db.commit()

    return ApiResponse(
        data={
            "id": memory_id,
            "deleted_conversations_count": len(associated_conversations),
            "diary_deleted": diary is not None
        },
        message="memory_deleted"
    )


@router.post("/memories/{memory_id}/past-self-chat", response_model=ApiResponse[dict])
def past_self_chat(
    memory_id: int,
    payload: PastSelfChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")

    chat_response, status_code = ChatService(db).send_message(
        user_id=user.id,
        request=ChatRequest(
            conversation_id=payload.conversation_id,
            mode=None if payload.conversation_id else "past_self",
            content=payload.message,
            use_memory=True,
            anchor_diary_id=None if payload.conversation_id else memory.diary_id,
        ),
    )
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=getattr(chat_response, "message", "past_self_chat_failed"))
    return ApiResponse(data=chat_response.model_dump(), message="past_self_chat_replied")
