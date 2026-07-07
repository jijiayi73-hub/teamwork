from fastapi import APIRouter

from ..schemas.conversations import (
    ConversationCreateResponse,
    ConversationHistoryResponse,
    ConversationMessageResponse,
    MessageCreateRequest,
)
from ..schemas.diaries import DiaryResponse
from ..services.conversation_service import add_message_and_reply, create_conversation, get_conversation
from ..services.diary_service import generate_and_save_diary


router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationCreateResponse)
def start_conversation():
    return create_conversation()


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
def read_conversation(conversation_id: str):
    return get_conversation(conversation_id)


@router.post("/{conversation_id}/messages", response_model=ConversationMessageResponse)
def create_message(conversation_id: str, payload: MessageCreateRequest):
    return add_message_and_reply(conversation_id, payload.content)


@router.post("/{conversation_id}/diary", response_model=DiaryResponse)
def create_diary_from_conversation(conversation_id: str):
    return generate_and_save_diary(conversation_id)
