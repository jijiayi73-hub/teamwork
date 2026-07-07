from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationMode(str, Enum):
    """Conversation mode enum"""
    COMPANION = "companion"
    PAST_SELF = "past_self"


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"


class MessageStatus(str, Enum):
    """Message status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, Enum):
    """Source type enum"""
    ANCHOR = "anchor"
    RETRIEVED = "retrieved"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    anchor_diary_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("diaries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        index=True
    )

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()"
    )

    __table_args__ = (
        CheckConstraint("mode IN ('companion', 'past_self')", name="ck_conversation_mode"),
        # Ensure mode and anchor_diary_id are consistent:
        # - companion mode must NOT have an anchor diary
        # - past_self mode MUST have an anchor diary
        CheckConstraint(
            "(mode = 'companion' AND anchor_diary_id IS NULL) OR (mode = 'past_self' AND anchor_diary_id IS NOT NULL)",
            name="ck_conversation_mode_anchor"
        ),
        Index("idx_conversations_user_deleted_updated", "user_id", "deleted_at", "updated_at"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    retrieval_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sources: Mapped[List["MessageSource"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageSource.rank.asc()"
    )

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
        CheckConstraint("status IN ('pending', 'completed', 'failed')", name="ck_message_status"),
        Index("idx_messages_conv_created", "conversation_id", "created_at"),
    )


class MessageSource(Base):
    """Source diary snapshot for a message.

    Snapshot semantics:
    - When a diary is used as a source, its relevant fields are snapshotted.
    - This allows historical sources to be displayed even if the original diary is deleted.
    - diary_id may become NULL after diary deletion, but snapshots remain intact.
    - Sources should only be associated with assistant messages (enforced at service layer).
    """
    __tablename__ = "message_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True
    )
    diary_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("diaries.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Snapshot fields - capture the state of the diary at the time of message creation
    diary_date_snapshot: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    title_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    excerpt_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_label_snapshot: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now
    )

    # Relationships
    message: Mapped["Message"] = relationship(back_populates="sources")

    __table_args__ = (
        CheckConstraint("source_type IN ('anchor', 'retrieved')", name="ck_source_type"),
        CheckConstraint("relevance_score >= 0.0 AND relevance_score <= 1.0", name="ck_relevance_score"),
        CheckConstraint("rank >= 1", name="ck_rank"),
        # Ensure no duplicate diary per message (when diary_id is not null)
        UniqueConstraint("message_id", "diary_id", name="uq_message_source_message_diary"),
        # Ensure no duplicate rank per message (for consistent ordering)
        UniqueConstraint("message_id", "rank", name="uq_message_source_message_rank"),
    )
