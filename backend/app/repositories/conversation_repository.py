from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.conversation import Conversation, ConversationMessage


def create_conversation(db: Session, conversation: Conversation) -> Conversation:
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def list_messages(db: Session, conversation_id: str) -> list[ConversationMessage]:
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(db.scalars(statement).all())


def list_user_messages(db: Session, conversation_id: str) -> list[ConversationMessage]:
    statement = (
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.role == "user",
        )
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(db.scalars(statement).all())


def add_messages(
    db: Session,
    conversation: Conversation,
    messages: list[ConversationMessage],
    updated_at: str,
) -> None:
    for message in messages:
        db.add(message)
    conversation.updated_at = updated_at
    db.commit()


def mark_diary_generated(db: Session, conversation: Conversation, updated_at: str) -> None:
    conversation.status = "diary_generated"
    conversation.updated_at = updated_at
    db.commit()
