from __future__ import annotations

from datetime import date
from unittest.mock import patch

from app.models.chat import Conversation, Message
from app.models.diary import Diary, EmotionAnalysis, Entry, User
from app.schemas.chat import ChatRequest, ConversationCreate
from app.services.chat_service import ChatService
from app.services.ai_provider import AIConfigError
from tests.chat_test_utils import FailedAIProvider, FakeAIProvider, TimeoutAIProvider


def create_user(db_session, name: str = "svcuser") -> User:
    user = User(
        username=name,
        email=f"{name}@example.com",
        password_hash="hash",
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_diary(db_session, user_id: int) -> Diary:
    entry = Entry(user_id=user_id, raw_content="memory", status="completed")
    db_session.add(entry)
    db_session.flush()
    analysis = EmotionAnalysis(
        entry_id=entry.id,
        primary_emotion="joy",
        emotion_score=5,
        valence=0.9,
        arousal=0.5,
        intensity=0.6,
        summary="summary",
        suggestion="suggestion",
    )
    db_session.add(analysis)
    db_session.flush()
    diary = Diary(
        user_id=user_id,
        entry_id=entry.id,
        analysis_id=analysis.id,
        title="Memory",
        content="A useful memory about joy",
        diary_date=date.today(),
    )
    db_session.add(diary)
    db_session.commit()
    db_session.refresh(diary)
    return diary


def provider_patch(provider):
    return patch("app.services.ai_provider.get_provider", return_value=provider)


def provider_config_error_patch(message: str = "openai package not installed"):
    return patch("app.services.ai_provider.get_provider", side_effect=AIConfigError(message))


def test_send_message_creates_persistent_conversation_and_messages(db_session):
    user = create_user(db_session)
    provider = FakeAIProvider()

    with provider_patch(provider):
        service = ChatService(db_session)
        response, status_code = service.send_message(
            user.id,
            ChatRequest(mode="companion", content="hello", use_memory=False),
        )

    assert status_code == 200
    assert response.conversation.message_count == 2
    assert db_session.query(Conversation).count() == 1
    assert db_session.query(Message).filter_by(role="user").count() == 1
    assert db_session.query(Message).filter_by(role="assistant").count() == 1


def test_existing_conversation_and_user_isolation(db_session):
    owner = create_user(db_session, "owner")
    other = create_user(db_session, "other")
    conv = Conversation(user_id=owner.id, mode="companion", title="private")
    db_session.add(conv)
    db_session.commit()

    service = ChatService(db_session)
    assert service.get_conversation(owner.id, conv.id) is not None
    assert service.get_conversation(other.id, conv.id) is None
    assert service.delete_conversation(other.id, conv.id) is None
    assert service.delete_conversation(owner.id, conv.id).deleted_conversation_id == conv.id
    assert service.get_conversation(owner.id, conv.id) is None


def test_past_self_anchor_validation(db_session):
    owner = create_user(db_session, "anchorowner")
    other = create_user(db_session, "anchorother")
    other_diary = create_diary(db_session, other.id)
    own_diary = create_diary(db_session, owner.id)
    service = ChatService(db_session)

    try:
        service.create_conversation(owner.id, ConversationCreate(mode="past_self"))
        assert False, "expected ValueError"
    except ValueError:
        pass

    try:
        service.create_conversation(
            owner.id,
            ConversationCreate(mode="past_self", anchor_diary_id=other_diary.id),
        )
        assert False, "expected ValueError"
    except ValueError:
        pass

    created = service.create_conversation(
        owner.id,
        ConversationCreate(mode="past_self", anchor_diary_id=own_diary.id),
    )
    assert created.conversation.anchor_diary_id == own_diary.id


def test_ai_failures_save_user_message_without_assistant(db_session):
    user = create_user(db_session, "failuser")

    with provider_patch(TimeoutAIProvider()):
        timeout_response, timeout_status = ChatService(db_session).send_message(
            user.id,
            ChatRequest(mode="companion", content="timeout", use_memory=False),
        )
    assert timeout_status == 504
    assert timeout_response["data"]["user_message"]["content"] == "timeout"
    assert db_session.query(Message).filter_by(role="user").count() == 1
    assert db_session.query(Message).filter_by(role="assistant").count() == 0

    with provider_patch(FailedAIProvider()):
        failed_response, failed_status = ChatService(db_session).send_message(
            user.id,
            ChatRequest(mode="companion", content="provider fail", use_memory=False),
        )
    assert failed_status == 502
    assert failed_response["message"] == "ai_service_unavailable"
    assert failed_response["error"]["details"]["provider"] in {"openai", "deepseek"}
    assert db_session.query(Message).filter_by(role="user").count() == 2
    assert db_session.query(Message).filter_by(role="assistant").count() == 0


def test_ai_config_error_is_returned_as_readable_502(db_session):
    user = create_user(db_session, "configuser")

    with provider_config_error_patch():
        response, status = ChatService(db_session).send_message(
            user.id,
            ChatRequest(mode="companion", content="hello", use_memory=False),
        )

    assert status == 502
    assert response["message"] == "ai_service_unavailable"
    assert response["error"]["details"]["provider_error"] == "openai package not installed"
    assert db_session.query(Message).filter_by(role="user").count() == 1
    assert db_session.query(Message).filter_by(role="assistant").count() == 0
