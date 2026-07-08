from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

from app.models.chat import Conversation, Message
from app.models.diary import Diary, EmotionAnalysis, Entry, User
from tests.chat_test_utils import FailedAIProvider, FakeAIProvider, TimeoutAIProvider


def auth(client, username: str, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "testpass123",
            "role": "user",
        },
    )
    assert response.status_code == 201
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_diary(db_session, user_id: int, title: str = "Anchor", days: int = 0) -> Diary:
    entry = Entry(user_id=user_id, raw_content=title, status="completed")
    db_session.add(entry)
    db_session.flush()
    analysis = EmotionAnalysis(
        entry_id=entry.id,
        primary_emotion="joy",
        emotion_score=5,
        valence=0.8,
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
        title=title,
        content=f"{title} content",
        diary_date=date.today() + timedelta(days=days),
    )
    db_session.add(diary)
    db_session.commit()
    db_session.refresh(diary)
    return diary


def provider_patch(provider):
    return patch("app.services.ai_provider.get_provider", return_value=provider)


def test_chat_routes_are_registered(client):
    routes = set(client.get("/openapi.json").json()["paths"].keys())
    assert "/api/v1/chat/messages" in routes
    assert "/api/v1/chat/conversations" in routes
    assert "/api/v1/chat/conversations/{conversation_id}" in routes
    assert "/api/v1/chat/conversations/{conversation_id}/messages" in routes


def test_send_message_success_persists_conversation_and_messages(client, auth_headers, db_session):
    provider = FakeAIProvider()
    provider.set_response("ok")
    with provider_patch(provider):
        response = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "hello", "use_memory": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["conversation"]["message_count"] == 2
    assert body["data"]["user_message"]["role"] == "user"
    assert body["data"]["assistant_message"]["role"] == "assistant"
    assert db_session.query(Conversation).count() == 1
    assert db_session.query(Message).count() == 2


def test_validation_and_auth_errors(client, auth_headers):
    no_token = client.post(
        "/api/v1/chat/messages",
        json={"mode": "companion", "content": "hello", "use_memory": False},
    )
    assert no_token.status_code == 401

    missing_mode = client.post(
        "/api/v1/chat/messages",
        headers=auth_headers,
        json={"content": "hello", "use_memory": False},
    )
    assert missing_mode.status_code == 422

    empty_content = client.post(
        "/api/v1/chat/messages",
        headers=auth_headers,
        json={"mode": "companion", "content": "", "use_memory": False},
    )
    assert empty_content.status_code == 422


def test_user_cannot_read_or_delete_other_users_conversation(client, db_session):
    user1_headers = auth(client, "owner", "owner@example.com")
    user2_headers = auth(client, "other", "other@example.com")
    owner = db_session.query(User).filter_by(username="owner").one()
    conv = Conversation(user_id=owner.id, mode="companion", title="private")
    db_session.add(conv)
    db_session.commit()

    get_response = client.get(f"/api/v1/chat/conversations/{conv.id}", headers=user2_headers)
    delete_response = client.delete(f"/api/v1/chat/conversations/{conv.id}", headers=user2_headers)

    assert get_response.status_code == 404
    assert delete_response.status_code == 404
    assert db_session.get(Conversation, conv.id).deleted_at is None
    assert client.get(f"/api/v1/chat/conversations/{conv.id}", headers=user1_headers).status_code == 200


def test_conversation_list_pagination_and_delete(client, auth_headers, db_session, test_user):
    for idx in range(3):
        db_session.add(Conversation(user_id=test_user["id"], mode="companion", title=f"c{idx}"))
    db_session.commit()

    page = client.get("/api/v1/chat/conversations?page=1&page_size=2", headers=auth_headers)
    assert page.status_code == 200
    assert page.json()["data"]["total"] == 3
    assert len(page.json()["data"]["conversations"]) == 2

    conv_id = page.json()["data"]["conversations"][0]["id"]
    deleted = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=auth_headers)
    assert deleted.status_code == 200
    listed = client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert listed.json()["data"]["total"] == 2


def test_get_messages_and_not_found(client, auth_headers, db_session, test_user):
    conv = Conversation(user_id=test_user["id"], mode="companion", title="history")
    db_session.add(conv)
    db_session.flush()
    db_session.add_all(
        [
            Message(conversation_id=conv.id, role="user", content="hi"),
            Message(conversation_id=conv.id, role="assistant", content="hello"),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/chat/conversations/{conv.id}/messages", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 2

    missing = client.get("/api/v1/chat/conversations/999999/messages", headers=auth_headers)
    assert missing.status_code == 404


def test_past_self_requires_user_owned_anchor(client, auth_headers, db_session, test_user):
    auth(client, "anchorother", "anchorother@example.com")
    other_user = db_session.query(User).filter_by(username="anchorother").one()
    other_diary = create_diary(db_session, other_user.id)

    response = client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={"mode": "past_self", "anchor_diary_id": other_diary.id},
    )
    assert response.status_code == 422

    own_diary = create_diary(db_session, test_user["id"])
    created = client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={"mode": "past_self", "anchor_diary_id": own_diary.id},
    )
    assert created.status_code == 201


def test_ai_timeout_and_provider_error_statuses_save_only_user_message(client, auth_headers, db_session):
    with provider_patch(TimeoutAIProvider()):
        timeout = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "timeout", "use_memory": False},
        )
    assert timeout.status_code == 504
    assert db_session.query(Message).filter_by(role="user").count() == 1
    assert db_session.query(Message).filter_by(role="assistant").count() == 0

    with provider_patch(FailedAIProvider()):
        failed = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "fail", "use_memory": False},
        )
    assert failed.status_code == 502
    assert failed.json()["error"]["details"]["provider"] in {"openai", "deepseek"}
    assert db_session.query(Message).filter_by(role="user").count() == 2
    assert db_session.query(Message).filter_by(role="assistant").count() == 0
