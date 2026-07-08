"""Chat API schemas for RAG-based conversation feature.

All schemas follow the API contract defined in:
docs/vibe-logs/log-07-rag-chat-api-design.md

API Contract Status: FROZEN (v1.2.1)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .common import ErrorCode


# ============================================================================
# Message Source Schemas
# ============================================================================


class MessageSource(BaseModel):
    """Source diary for new message response (no snapshot fields).

    Used in ChatResponse for immediate display of retrieved sources.
    """
    diary_id: int
    diary_date: date
    title: str
    excerpt: str  # First 100 characters
    emotion_label: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_type: Literal["anchor", "retrieved"]


class MessageSourceRead(BaseModel):
    """Message source from message_sources table (with snapshot fields).

    Used in ChatHistoryItem for historical message display.
    Snapshot fields preserve source display even after diary deletion.
    """
    id: int
    diary_id: int | None  # NULL if diary was deleted
    source_type: Literal["anchor", "retrieved"]
    # Snapshot fields - persist even after diary deletion
    diary_date_snapshot: date | None
    title_snapshot: str
    excerpt_snapshot: str
    emotion_label_snapshot: str | None
    relevance_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


# ============================================================================
# Metadata Schemas
# ============================================================================


class RetrievalMetadata(BaseModel):
    """Information about how historical context was retrieved."""
    used: bool
    strategy: str
    total_found: int = Field(ge=0)
    used_in_context: int = Field(ge=0)


class SafetyCheck(BaseModel):
    """Content safety check result with structured enums."""
    flagged: bool
    level: Literal["none", "low", "medium", "high"]
    category: Literal["emotional_distress", "self_harm_risk", "violence_risk"] | None
    action: Literal["none", "show_notice", "suggest_support", "trigger_emergency_flow"]


# ============================================================================
# Message Schemas
# ============================================================================


class MessageRead(BaseModel):
    """Basic message representation without sources.

    Use ChatHistoryItem for messages with sources.
    """
    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatHistoryItem(BaseModel):
    """Message in conversation history with optional sources.

    User messages have empty sources array.
    Assistant messages include all sources from message_sources table.
    """
    message: MessageRead
    sources: list[MessageSourceRead]  # Empty for user messages


# ============================================================================
# Conversation Schemas
# ============================================================================


class ConversationRead(BaseModel):
    """Conversation returned to frontend.

    Note: user_id is NOT returned - exists only in database and auth context.
    """
    id: int
    mode: Literal["companion", "past_self"]
    title: str | None
    anchor_diary_id: int | None
    started_at: datetime
    updated_at: datetime
    message_count: int = Field(ge=0)


# ============================================================================
# Request/Response Schemas
# ============================================================================


class ChatRequest(BaseModel):
    """Request for POST /api/v1/chat/messages."""
    conversation_id: int | None = None
    mode: Literal["companion", "past_self"] | None = None
    content: str = Field(min_length=1, max_length=5000)
    use_memory: bool = False
    anchor_diary_id: int | None = None

    @model_validator(mode="after")
    def validate_business_rules(self) -> ChatRequest:
        """Validate business rules for chat requests.

        Rules:
        - mode is required when creating new conversation (conversation_id is None)
        - anchor_diary_id is required for past_self mode when creating new conversation
        """
        # Business rule: mode required for new conversation
        if self.conversation_id is None and self.mode is None:
            raise ValueError("mode is required when creating a new conversation")

        # Business rule: past_self requires anchor_diary_id
        if self.mode == "past_self" and self.anchor_diary_id is None:
            raise ValueError("anchor_diary_id is required for past_self mode")

        return self


class ChatResponse(BaseModel):
    """Response for POST /api/v1/chat/messages.

    Note: No top-level created_at - use assistant_message.created_at as timestamp.
    """
    conversation: ConversationRead
    user_message: MessageRead
    assistant_message: MessageRead
    retrieval: RetrievalMetadata
    sources: list[MessageSource]  # Single source of truth
    safety: SafetyCheck


class ConversationCreate(BaseModel):
    """Request for POST /api/v1/chat/conversations."""
    mode: Literal["companion", "past_self"]
    title: str | None = None
    anchor_diary_id: int | None = None

    @model_validator(mode="after")
    def validate_past_self_requires_anchor(self) -> ConversationCreate:
        """Validate that past_self mode has anchor_diary_id."""
        if self.mode == "past_self" and self.anchor_diary_id is None:
            raise ValueError("anchor_diary_id is required for past_self mode")
        return self


class ConversationListResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations."""
    conversations: list[ConversationRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class ConversationDetailResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations/{id}."""
    conversation: ConversationRead


class MessageListResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations/{id}/messages."""
    messages: list[ChatHistoryItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class DeleteConversationResponse(BaseModel):
    """Response for DELETE /api/v1/chat/conversations/{id}."""
    deleted_conversation_id: int


# ============================================================================
# Error Response Extensions
# ============================================================================


class ChatErrorResponse(BaseModel):
    """Extended error response for chat endpoints."""
    success: bool = False
    data: None = None
    message: str
    request_id: str
    error_code: ErrorCode
    error: ErrorDetail


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: ErrorCode
    message: str
    details: dict | None = None
