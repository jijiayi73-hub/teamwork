"""Chat router for RAG-based conversation feature.

Implements all 6 endpoints defined in the API contract:
- POST /api/v1/chat/messages
- GET /api/v1/chat/conversations
- POST /api/v1/chat/conversations
- GET /api/v1/chat/conversations/{id}
- GET /api/v1/chat/conversations/{id}/messages
- DELETE /api/v1/chat/conversations/{id}

API Contract: docs/vibe-logs/log-07-rag-chat-api-design.md
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import User
from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationRead,
    DeleteConversationResponse,
    MessageListResponse,
)
from ..schemas.common import ApiResponse, ErrorCode, ErrorResponse
from ..services.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# POST /api/v1/chat/messages - Send message
# ============================================================================


@router.post(
    "/messages",
    response_model=ApiResponse[ChatResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send message and get AI response.

    Creates a new conversation if conversation_id is not provided.
    Retrieves context based on use_memory and mode.
    Generates AI response with retrieved context.

    Args:
        request: Chat request with message and metadata
        user: Current authenticated user
        db: Database session

    Returns:
        ChatResponse with conversation, messages, sources, and safety info

    Raises:
        401: Not authenticated
        404: Conversation or anchor diary not found
        422: Validation error
        429: Rate limit exceeded
        502: AI provider error
        504: AI timeout
    """
    service = ChatService(db)
    response_data, status_code = service.send_message(user.id, request)

    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(response_data),
        )

    return ApiResponse(data=response_data, message="message_sent")


# ============================================================================
# GET /api/v1/chat/conversations - List conversations
# ============================================================================


@router.get(
    "/conversations",
    response_model=ApiResponse[ConversationListResponse],
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def list_conversations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    mode: Literal["companion", "past_self"] | None = Query(
        None, description="Filter by conversation mode"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's conversations.

    Supports pagination and optional mode filtering.
    Sorted by updated_at descending (most recent first).

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        mode: Optional mode filter
        user: Current authenticated user
        db: Database session

    Returns:
        ConversationListResponse with conversations and pagination info
    """
    service = ChatService(db)
    result = service.list_conversations(user.id, page, page_size, mode)
    return ApiResponse(data=result, message="conversations_retrieved")


# ============================================================================
# POST /api/v1/chat/conversations - Create conversation
# ============================================================================


@router.post(
    "/conversations",
    response_model=ApiResponse[ConversationDetailResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def create_conversation(
    request: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new conversation.

    For past_self mode, anchor_diary_id is required.

    Args:
        request: Conversation create request
        user: Current authenticated user
        db: Database session

    Returns:
        ConversationDetailResponse with created conversation

    Raises:
        401: Not authenticated
        422: Validation error (e.g., past_self without anchor)
    """
    service = ChatService(db)

    try:
        result = service.create_conversation(user.id, request)
        return ApiResponse(data=result, message="conversation_created")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


# ============================================================================
# GET /api/v1/chat/conversations/{id} - Get conversation
# ============================================================================


@router.get(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[ConversationDetailResponse],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation metadata by ID.

    Does not include messages - use /conversations/{id}/messages for that.

    Args:
        conversation_id: Conversation ID
        user: Current authenticated user
        db: Database session

    Returns:
        ConversationDetailResponse with conversation metadata

    Raises:
        401: Not authenticated
        404: Conversation not found (or access denied)
    """
    service = ChatService(db)
    result = service.get_conversation(user.id, conversation_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="conversation_not_found",
        )

    return ApiResponse(data=result, message="conversation_retrieved")


# ============================================================================
# GET /api/v1/chat/conversations/{id}/messages - Get messages
# ============================================================================


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[MessageListResponse],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages for a conversation.

    Supports pagination for infinite scroll.
    Messages include sources for assistant responses.

    Args:
        conversation_id: Conversation ID
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        user: Current authenticated user
        db: Database session

    Returns:
        MessageListResponse with messages and sources

    Raises:
        401: Not authenticated
        404: Conversation not found (or access denied)
    """
    service = ChatService(db)
    result = service.get_messages(user.id, conversation_id, page, page_size)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="conversation_not_found",
        )

    return ApiResponse(data=result, message="messages_retrieved")


# ============================================================================
# DELETE /api/v1/chat/conversations/{id} - Delete conversation
# ============================================================================


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[DeleteConversationResponse],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete conversation (soft delete).

    Marks conversation as deleted. Messages and sources cascade delete.
    Original diary entries are NOT affected.

    Args:
        conversation_id: Conversation ID
        user: Current authenticated user
        db: Database session

    Returns:
        DeleteConversationResponse with deleted conversation ID

    Raises:
        401: Not authenticated
        404: Conversation not found (or access denied)
    """
    service = ChatService(db)
    result = service.delete_conversation(user.id, conversation_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="conversation_not_found",
        )

    return ApiResponse(data=result, message="conversation_deleted")
