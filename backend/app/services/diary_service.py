from uuid import uuid4

from fastapi import HTTPException, status

from ..database import SessionLocal
from ..models.diary import Diary
from ..repositories import conversation_repository, diary_repository
from .conversation_service import list_user_messages, model_to_dict, utc_now


def generate_and_save_diary(conversation_id: str) -> dict:
    user_messages = list_user_messages(conversation_id)
    if not user_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate diary from an empty conversation",
        )

    diary = build_diary_from_messages(conversation_id, user_messages)
    now = utc_now()
    diary_id = str(uuid4())

    with SessionLocal() as db:
        conversation = conversation_repository.get_conversation(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        existing = diary_repository.get_diary_by_conversation(db, conversation_id)
        if existing is not None:
            existing.title = diary["title"]
            existing.content = diary["content"]
            existing.mood = diary["mood"]
            existing.summary = diary["summary"]
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            return model_to_dict(existing)

        saved_diary = diary_repository.save_diary(
            db,
            Diary(
                id=diary_id,
                conversation_id=conversation_id,
                title=diary["title"],
                content=diary["content"],
                mood=diary["mood"],
                summary=diary["summary"],
                created_at=now,
                updated_at=now,
            ),
        )
        conversation_repository.mark_diary_generated(db, conversation, updated_at=now)

    return model_to_dict(saved_diary)


def get_diary(diary_id: str) -> dict:
    with SessionLocal() as db:
        diary = diary_repository.get_diary(db, diary_id)
        if diary is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diary not found")
        return model_to_dict(diary)


def list_diaries(page: int = 1, page_size: int = 20) -> list[dict]:
    with SessionLocal() as db:
        diaries = diary_repository.list_diaries(db, page=page, page_size=page_size)
        return [model_to_dict(diary) for diary in diaries]


def build_diary_from_messages(conversation_id: str, messages: list[dict]) -> dict:
    contents = [message["content"].strip() for message in messages if message["content"].strip()]
    combined = "\n".join(f"{index + 1}. {content}" for index, content in enumerate(contents))
    mood = infer_mood(" ".join(contents))
    title = build_title(contents[0])
    summary = f"这篇日记整理自 {len(contents)} 条记录，主要情绪是{mood}。"
    content = (
        f"# {title}\n\n"
        f"今天的记录里，我反复提到：\n\n{combined}\n\n"
        f"把这些话放在一起看，这一天的核心感受更接近“{mood}”。"
        "我允许自己先如实记下这些经历，再慢慢决定接下来怎么照顾自己。"
    )

    return {
        "conversation_id": conversation_id,
        "title": title,
        "content": content,
        "mood": mood,
        "summary": summary,
    }


def infer_mood(text: str) -> str:
    mood_keywords = {
        "低落": ("难过", "失望", "委屈", "考砸", "伤心"),
        "焦虑": ("焦虑", "压力", "害怕", "担心", "紧张"),
        "疲惫": ("累", "疲惫", "困", "撑不住"),
        "愉快": ("开心", "高兴", "顺利", "舒服", "喜欢"),
        "期待": ("期待", "希望", "想要", "计划"),
    }
    for mood, keywords in mood_keywords.items():
        if any(keyword in text for keyword in keywords):
            return mood
    return "平静"


def build_title(first_message: str) -> str:
    clean = " ".join(first_message.split())
    if len(clean) <= 18:
        return clean
    return f"{clean[:18]}..."
