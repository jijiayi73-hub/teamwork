from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from ..database import SessionLocal
from ..models.conversation import Conversation, ConversationMessage
from ..repositories import conversation_repository


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_to_dict(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def create_conversation() -> dict:
    now = utc_now()
    conversation_id = str(uuid4())

    with SessionLocal() as db:
        conversation_repository.create_conversation(
            db,
            Conversation(id=conversation_id, status="open", created_at=now, updated_at=now),
        )

    return {
        "conversation_id": conversation_id,
        "status": "open",
        "created_at": now,
    }


def get_conversation(conversation_id: str) -> dict:
    with SessionLocal() as db:
        conversation = conversation_repository.get_conversation(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        messages = conversation_repository.list_messages(db, conversation_id)

    data = model_to_dict(conversation)
    data["conversation_id"] = data.pop("id")
    data["messages"] = [model_to_dict(message) for message in messages]
    return data


def add_message_and_reply(conversation_id: str, content: str) -> dict:
    content = content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message content is empty")

    now = utc_now()
    user_message = {
        "id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": "user",
        "content": content,
        "created_at": now,
    }
    assistant_content = build_companion_reply(content)
    assistant_message = {
        "id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": assistant_content,
        "created_at": utc_now(),
    }

    with SessionLocal() as db:
        conversation = conversation_repository.get_conversation(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        conversation_repository.add_messages(
            db,
            conversation,
            [
                ConversationMessage(**user_message),
                ConversationMessage(**assistant_message),
            ],
            updated_at=assistant_message["created_at"],
        )

    return {
        "user_message": user_message,
        "assistant_message": assistant_message,
    }


def list_user_messages(conversation_id: str) -> list[dict]:
    with SessionLocal() as db:
        conversation = conversation_repository.get_conversation(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        messages = conversation_repository.list_user_messages(db, conversation_id)

    return [model_to_dict(message) for message in messages]


def build_companion_reply(content: str) -> str:
    negative_words = ("难过", "焦虑", "崩溃", "累", "烦", "害怕", "失望", "压力", "考砸", "委屈")
    positive_words = ("开心", "顺利", "喜欢", "完成", "进步", "舒服", "期待", "高兴")

    if any(word in content for word in negative_words):
        return "我听见你现在不太好受。先把这件事放在这里就已经很不容易了，我们可以慢慢把它讲清楚。"
    if any(word in content for word in positive_words):
        return "这听起来是一个值得被认真记下来的时刻。你可以继续说说，最让你有感觉的部分是什么？"
    if "?" in content or "？" in content:
        return "这个问题背后好像也有一些情绪和期待。你愿意再说一点当时发生了什么吗？"
    return "我在听。你可以继续写下今天发生的事、身体的感觉，或者脑子里一直绕着的那句话。"
