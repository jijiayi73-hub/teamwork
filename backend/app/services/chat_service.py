"""Chat service for RAG-based conversation feature.

This service handles all business logic for the chat feature:
- Conversation management (create, list, get, delete)
- Message sending with AI response generation
- Retrieval integration for context
- Safety checking
- Source snapshot creation
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from ..models.chat import Conversation, Message, MessageSource
from ..utils.emotions import normalize_emotion_label
from ..models.diary import Diary
from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationRead,
    DeleteConversationResponse,
    MessageListResponse,
    MessageRead,
    MessageSource as MessageSourceSchema,
    ChatHistoryItem,
    MessageSourceRead,
    RetrievalMetadata,
    SafetyCheck,
)
from .ai_provider import (
    AIConfigError,
    AIProvider,
    AITimeoutError,
    AIProviderError,
    AIRateLimitError,
    AIResponse,
)
from .retrieval_service import retrieve_context, RetrievedDiary
from .safety_service import SafetyService, SafetyCheck as SafetyCheckData


# ============================================================================
# Helper Functions
# ============================================================================


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_request_id() -> str:
    """Generate unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def generate_conversation_title(
    mode: Literal["companion", "past_self"],
    first_message: str,
    anchor_diary: Diary | None = None,
) -> str:
    """Generate conversation title based on mode and context.

    Args:
        mode: Conversation mode
        first_message: First user message
        anchor_diary: Anchor diary (for past_self mode)

    Returns:
        Generated title
    """
    if mode == "past_self" and anchor_diary:
        return f"回忆：{anchor_diary.diary_date} 的记忆"

    # For companion mode, use first message excerpt
    return first_message[:30] + "..." if len(first_message) > 30 else first_message


# ============================================================================
# Main Chat Service
# ============================================================================


class ChatService:
    """Service for managing conversations and messages."""

    def __init__(self, db: Session):
        """Initialize chat service.

        Args:
            db: Database session
        """
        self.db = db
        self.ai_provider = None
        self.safety_service = SafetyService()

    def _get_ai_provider(self) -> AIProvider:
        """Get AI provider instance."""
        from .ai_provider import get_provider
        from ..config import settings

        # Use provider from config if available, otherwise default to openai
        provider = settings.ai_provider
        model = settings.ai_default_model if settings.ai_provider == provider else None
        base_url = settings.deepseek_base_url if provider == "deepseek" else None

        return get_provider(
            provider=provider,
            default_model=model,
            base_url=base_url,
            timeout=settings.ai_timeout,
        )

    # ========================================================================
    # Send Message
    # ========================================================================

    def send_message(
        self,
        user_id: int,
        request: ChatRequest,
    ) -> tuple[ChatResponse | dict, int]:
        """Send message and get AI response.

        Args:
            user_id: Current user ID
            request: Chat request

        Returns:
            Tuple of (response, status_code)

            On success: (ChatResponse, 200)
            On AI failure: (error_response, 502 or 504)
        """
        request_id = generate_request_id()

        try:
            # Get or create conversation
            if request.conversation_id:
                conversation = self._get_conversation_for_user(
                    user_id, request.conversation_id
                )
                if not conversation:
                    return self._not_found_response("conversation_not_found", request_id), 404

                mode = conversation.mode
                anchor_diary_id = conversation.anchor_diary_id
                is_followup = True
            else:
                # New conversation
                mode = request.mode
                anchor_diary_id = request.anchor_diary_id
                is_followup = False

                # Validate mode and anchor consistency
                if mode == "past_self":
                    if not anchor_diary_id:
                        return self._validation_response(
                            "anchor_diary_id required for past_self mode", request_id
                        ), 422

                    # Verify anchor diary exists and belongs to user
                    anchor_diary = self._get_diary_for_user(user_id, anchor_diary_id)
                    if not anchor_diary:
                        return self._not_found_response("diary_not_found", request_id), 404
                else:
                    anchor_diary = None

                # Create conversation
                conversation = Conversation(
                    user_id=user_id,
                    mode=mode,
                    title="",  # Will be set after first message
                    anchor_diary_id=anchor_diary_id,
                )
                self.db.add(conversation)
                self.db.flush()  # Get ID without committing

            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=request.content,
                status="completed",
            )
            self.db.add(user_message)
            self.db.flush()

            # Update conversation title on first user message.
            existing_message_count = (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .count()
            )
            if existing_message_count == 1:
                conversation.title = generate_conversation_title(
                    mode, request.content, anchor_diary if mode == "past_self" else None
                )

            # AI decides whether to retrieve historical context
            # This replaces the old use_memory parameter from frontend
            ai_provider = self.ai_provider or self._get_ai_provider()
            self.ai_provider = ai_provider

            should_retrieve, retrieve_reasoning = ai_provider.should_retrieve_context(
                user_message=request.content,
                mode=mode,
            )

            # For past_self mode, always retrieve (the anchor is the context)
            if mode == "past_self":
                effective_use_memory = True
            else:
                effective_use_memory = should_retrieve

            # Retrieve context based on AI decision
            retrieved_diaries, strategy_name = retrieve_context(
                db=self.db,
                user_id=user_id,
                query=request.content,
                use_memory=effective_use_memory,
                mode=mode,
                anchor_diary_id=anchor_diary_id,
                is_followup=is_followup,
            )

            # Build context string for AI
            context = self._build_context_string(retrieved_diaries)

            # Get conversation history
            messages = self._get_conversation_messages(conversation.id)

            # Generate AI response
            try:
                ai_provider = self.ai_provider or self._get_ai_provider()
                self.ai_provider = ai_provider
                ai_response = ai_provider.generate_response(
                    messages=messages,
                    context=context,
                    mode=mode,
                )

                # Create assistant message
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=ai_response.content,
                    status="completed",
                    retrieval_used=len(retrieved_diaries) > 0,
                    model_name=ai_response.model_name,
                    latency_ms=ai_response.latency_ms,
                    token_usage_input=ai_response.token_usage_input,
                    token_usage_output=ai_response.token_usage_output,
                )
                self.db.add(assistant_message)
                self.db.flush()

                # Create message sources
                for rank, retrieved in enumerate(retrieved_diaries, start=1):
                    self._create_message_source(
                        assistant_message.id,
                        retrieved.diary,
                        retrieved.relevance_score,
                        retrieved.source_type,
                        rank,
                    )

                # Safety check
                safety = self.safety_service.check_content_safety(request.content)
                safety_result = SafetyCheck(
                    flagged=safety.flagged,
                    level=safety.level,
                    category=safety.category,
                    action=safety.action,
                )

                # Update conversation
                conversation.updated_at = utc_now()

                self.db.commit()

                # Build response
                return (
                    self._build_chat_response(
                        conversation=conversation,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        retrieved_diaries=retrieved_diaries,
                        strategy_name=strategy_name,
                        safety=safety_result,
                    ),
                    200,
                )

            except AIRateLimitError:
                self.db.commit()
                return self._rate_limit_response(request_id), 429

            except AITimeoutError:
                self.db.commit()
                return (
                    self._ai_timeout_response(
                        conversation=conversation,
                        user_message=user_message,
                        request_id=request_id,
                    ),
                    504,
                )

            except AIConfigError as e:
                self.db.commit()
                return (
                    self._ai_error_response(
                        str(e), request_id
                    ),
                    502,
                )

            except AIProviderError as e:
                self.db.commit()
                return (
                    self._ai_error_response(
                        str(e), request_id
                    ),
                    502,
                )

        except Exception as e:
            self.db.rollback()
            raise

    # ========================================================================
    # Conversation Management
    # ========================================================================

    def list_conversations(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        mode: Literal["companion", "past_self"] | None = None,
    ) -> ConversationListResponse:
        """List user's conversations.

        Args:
            user_id: Current user ID
            page: Page number (1-indexed)
            page_size: Items per page
            mode: Optional mode filter

        Returns:
            Conversation list response
        """
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )

        if mode:
            query = query.filter(Conversation.mode == mode)

        # Get total count
        total = query.count()

        # Paginate
        offset = (page - 1) * page_size
        conversations = (
            query.order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return ConversationListResponse(
            conversations=[self._conversation_to_read(c) for c in conversations],
            page=page,
            page_size=page_size,
            total=total,
        )

    def create_conversation(
        self,
        user_id: int,
        request: ConversationCreate,
    ) -> ConversationDetailResponse:
        """Create new conversation.

        Args:
            user_id: Current user ID
            request: Conversation create request

        Returns:
            Conversation detail response
        """
        # Validate past_self requires anchor
        if request.mode == "past_self" and not request.anchor_diary_id:
            raise ValueError("anchor_diary_id required for past_self mode")

        # Verify anchor diary exists
        anchor_diary = None
        if request.anchor_diary_id:
            anchor_diary = self._get_diary_for_user(user_id, request.anchor_diary_id)
            if not anchor_diary:
                raise ValueError("anchor diary not found")

        conversation = Conversation(
            user_id=user_id,
            mode=request.mode,
            title=request.title or "新对话",
            anchor_diary_id=request.anchor_diary_id,
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return ConversationDetailResponse(
            conversation=self._conversation_to_read(conversation)
        )

    def get_conversation(
        self,
        user_id: int,
        conversation_id: int,
    ) -> ConversationDetailResponse | None:
        """Get conversation by ID.

        Args:
            user_id: Current user ID
            conversation_id: Conversation ID

        Returns:
            Conversation detail response or None if not found
        """
        conversation = self._get_conversation_for_user(user_id, conversation_id)
        if not conversation:
            return None

        return ConversationDetailResponse(
            conversation=self._conversation_to_read(conversation)
        )

    def delete_conversation(
        self,
        user_id: int,
        conversation_id: int,
    ) -> DeleteConversationResponse | None:
        """Delete conversation (soft delete).

        Args:
            user_id: Current user ID
            conversation_id: Conversation ID

        Returns:
            Delete response or None if not found
        """
        conversation = self._get_conversation_for_user(user_id, conversation_id)
        if not conversation:
            return None

        conversation.deleted_at = utc_now()
        self.db.commit()

        return DeleteConversationResponse(deleted_conversation_id=conversation_id)

    # ========================================================================
    # Message History
    # ========================================================================

    def get_messages(
        self,
        user_id: int,
        conversation_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> MessageListResponse | None:
        """Get messages for a conversation.

        Args:
            user_id: Current user ID
            conversation_id: Conversation ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Message list response or None if conversation not found
        """
        # Verify conversation exists and belongs to user
        conversation = self._get_conversation_for_user(user_id, conversation_id)
        if not conversation:
            return None

        # Get messages
        offset = (page - 1) * page_size
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Get total count
        total = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

        # Build response with sources
        history_items = []
        for msg in messages:
            message_read = MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,  # type: ignore
                content=msg.content,
                created_at=msg.created_at,
            )

            # Get sources for assistant messages
            sources = []
            if msg.role == "assistant":
                msg_sources = (
                    self.db.query(MessageSource)
                    .filter(MessageSource.message_id == msg.id)
                    .order_by(MessageSource.rank.asc())
                    .all()
                )

                for ms in msg_sources:
                    sources.append(
                        MessageSourceRead(
                            id=ms.id,
                            diary_id=ms.diary_id,
                            source_type=ms.source_type,  # type: ignore
                            diary_date_snapshot=ms.diary_date_snapshot,
                            title_snapshot=ms.title_snapshot,
                            excerpt_snapshot=ms.excerpt_snapshot,
                            emotion_label_snapshot=ms.emotion_label_snapshot,
                            relevance_score=ms.relevance_score,
                            rank=ms.rank,
                        )
                    )

            history_items.append(
                ChatHistoryItem(message=message_read, sources=sources)
            )

        return MessageListResponse(
            messages=history_items,
            page=page,
            page_size=page_size,
            total=total,
        )

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _get_conversation_for_user(
        self, user_id: int, conversation_id: int
    ) -> Conversation | None:
        """Get conversation if it exists and belongs to user."""
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .first()
        )

    def _get_diary_for_user(self, user_id: int, diary_id: int) -> Diary | None:
        """Get diary if it exists and belongs to user."""
        return (
            self.db.query(Diary)
            .filter(
                Diary.id == diary_id,
                Diary.user_id == user_id,
                Diary.deleted_at.is_(None),
            )
            .first()
        )

    def _get_conversation_messages(
        self, conversation_id: int, limit: int = 10
    ) -> list[dict]:
        """Get recent messages for AI context.

        Returns list of {role, content} dicts for OpenAI API.
        """
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        # Reverse to get chronological order
        messages.reverse()

        return [
            {"role": msg.role, "content": msg.content}  # type: ignore
            for msg in messages
            if msg.role in ("user", "assistant")
        ]

    def _build_context_string(self, retrieved_diaries: list[RetrievedDiary]) -> str:
        """Build context string from retrieved diaries."""
        if not retrieved_diaries:
            return ""

        context_parts = []
        for retrieved in retrieved_diaries:
            diary = retrieved.diary
            emotion = normalize_emotion_label(diary.analysis.primary_emotion if diary.analysis else None)
            context_parts.append(
                f"日期：{diary.diary_date}\n"
                f"标题：{diary.title}\n"
                f"内容：{diary.content[:200]}...\n"
                f"情绪：{emotion}"
            )

        return "\n---\n".join(context_parts)

    def _create_message_source(
        self,
        message_id: int,
        diary: Diary,
        relevance_score: float,
        source_type: str,
        rank: int,
    ) -> None:
        """Create message source with snapshot fields."""
        emotion = normalize_emotion_label(diary.analysis.primary_emotion if diary.analysis else None)
        source = MessageSource(
            message_id=message_id,
            diary_id=diary.id,
            source_type=source_type,
            diary_date_snapshot=diary.diary_date,
            title_snapshot=diary.title,
            excerpt_snapshot=diary.content[:100],
            emotion_label_snapshot=emotion,
            relevance_score=relevance_score,
            rank=rank,
        )
        self.db.add(source)

    def _conversation_to_read(self, conversation: Conversation) -> ConversationRead:
        """Convert Conversation model to ConversationRead schema."""
        return ConversationRead(
            id=conversation.id,
            mode=conversation.mode,  # type: ignore
            title=conversation.title,
            anchor_diary_id=conversation.anchor_diary_id,
            started_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=(
                self.db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .count()
            ),
        )

    def _build_chat_response(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        retrieved_diaries: list[RetrievedDiary],
        strategy_name: str,
        safety: SafetyCheckData,
    ) -> ChatResponse:
        """Build ChatResponse from models."""
        # Build sources list
        sources = []
        for retrieved in retrieved_diaries:
            emotion = normalize_emotion_label(retrieved.diary.analysis.primary_emotion if retrieved.diary.analysis else None)
            sources.append(
                MessageSourceSchema(
                    diary_id=retrieved.diary.id,
                    diary_date=retrieved.diary.diary_date,
                    title=retrieved.diary.title,
                    excerpt=retrieved.diary.content[:100],
                    emotion_label=emotion,
                    relevance_score=retrieved.relevance_score,
                    source_type=retrieved.source_type,  # type: ignore
                )
            )

        return ChatResponse(
            conversation=self._conversation_to_read(conversation),
            user_message=MessageRead(
                id=user_message.id,
                conversation_id=user_message.conversation_id,
                role=user_message.role,  # type: ignore
                content=user_message.content,
                created_at=user_message.created_at,
            ),
            assistant_message=MessageRead(
                id=assistant_message.id,
                conversation_id=assistant_message.conversation_id,
                role=assistant_message.role,  # type: ignore
                content=assistant_message.content,
                created_at=assistant_message.created_at,
            ),
            retrieval=RetrievalMetadata(
                used=len(retrieved_diaries) > 0,
                strategy=strategy_name,
                total_found=len(retrieved_diaries),
                used_in_context=len(retrieved_diaries),
            ),
            sources=sources,
            safety=SafetyCheck(
                flagged=safety.flagged,
                level=safety.level,
                category=safety.category,
                action=safety.action,
            ),
        )

    # ========================================================================
    # Error Response Builders
    # ========================================================================

    def _not_found_response(self, detail: str, request_id: str) -> dict:
        """Build 404 error response."""
        from ..schemas.common import ErrorCode
        return {
            "success": False,
            "data": None,
            "message": detail,
            "request_id": request_id,
            "error_code": ErrorCode.NOT_FOUND,
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": "Resource not found",
                "details": {"detail": detail},
            },
        }

    def _validation_response(self, message: str, request_id: str) -> dict:
        """Build 422 error response."""
        from ..schemas.common import ErrorCode
        return {
            "success": False,
            "data": None,
            "message": "validation_failed",
            "request_id": request_id,
            "error_code": ErrorCode.VALIDATION_ERROR,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": message,
                "details": None,
            },
        }

    def _ai_timeout_response(
        self, conversation: Conversation, user_message: Message, request_id: str
    ) -> dict:
        """Build 504 timeout response."""
        from ..schemas.common import ErrorCode
        return {
            "success": False,
            "data": {
                "conversation": self._conversation_to_read(conversation).model_dump(),
                "user_message": MessageRead(
                    id=user_message.id,
                    conversation_id=user_message.conversation_id,
                    role=user_message.role,  # type: ignore
                    content=user_message.content,
                    created_at=user_message.created_at,
                ).model_dump(),
            },
            "message": "ai_service_timeout",
            "request_id": request_id,
            "error_code": ErrorCode.INTERNAL_ERROR,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "AI service request timed out",
                "details": {
                    "timeout_seconds": 30,
                    "user_message_saved": True,
                },
            },
        }

    def _ai_error_response(self, error_message: str, request_id: str) -> dict:
        """Build 502 provider error response."""
        from ..config import settings
        from ..schemas.common import ErrorCode
        return {
            "success": False,
            "data": None,
            "message": "ai_service_unavailable",
            "request_id": request_id,
            "error_code": ErrorCode.INTERNAL_ERROR,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "AI service is temporarily unavailable",
                "details": {
                    "provider": settings.ai_provider,
                    "provider_error": error_message,
                },
            },
        }

    def _rate_limit_response(self, request_id: str) -> dict:
        """Build 429 rate limit response."""
        from ..schemas.common import ErrorCode
        return {
            "success": False,
            "data": None,
            "message": "rate_limited",
            "request_id": request_id,
            "error_code": ErrorCode.VALIDATION_ERROR,  # Should be RATE_LIMITED but using existing code
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": 60,
                    "limit_type": "messages per minute",
                },
            },
        }
