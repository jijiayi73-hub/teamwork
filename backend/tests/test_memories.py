from unittest.mock import patch

from tests.chat_test_utils import FakeAIProvider


def create_memory(client, auth_headers, sample_diary, **overrides):
    payload = {
        "diary_id": sample_diary["id"],
        "cover_image_url": "/uploads/demo.png",
        "cover_prompt": "soft garden cover",
        "emotion_label": "calm",
        "emotion_color": "#8fb8ff",
        "keywords": ["quiet", "garden"],
        "conversation_summary": "user and assistant talked about today",
    }
    payload.update(overrides)
    return client.post("/api/v1/memories", headers=auth_headers, json=payload)


def test_create_list_get_and_delete_memory_card(client, auth_headers, sample_diary):
    created = create_memory(client, auth_headers, sample_diary)

    assert created.status_code == 201
    memory = created.json()["data"]
    assert memory["diary_id"] == sample_diary["id"]
    assert memory["cover_image_url"] == "/uploads/demo.png"
    assert memory["emotion_label"] == "calm"
    assert memory["emotion_color"] == "#8fb8ff"
    assert memory["keywords"] == ["quiet", "garden"]
    assert memory["diary"]["content"] == sample_diary["content"]

    listed = client.get("/api/v1/memories?emotion=calm&keyword=garden", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    detail = client.get(f"/api/v1/memories/{memory['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == memory["id"]

    deleted = client.delete(f"/api/v1/memories/{memory['id']}", headers=auth_headers)
    assert deleted.status_code == 200
    assert client.get("/api/v1/memories", headers=auth_headers).json()["data"] == []


def test_memory_card_isolated_by_user(client, auth_headers, admin_headers, sample_diary):
    memory = create_memory(client, auth_headers, sample_diary).json()["data"]
    response = client.get(f"/api/v1/memories/{memory['id']}", headers=admin_headers)
    assert response.status_code == 404


def test_past_self_chat_uses_backend_chat_service(client, auth_headers, sample_diary):
    memory = create_memory(client, auth_headers, sample_diary).json()["data"]
    provider = FakeAIProvider()
    provider.set_response("past self reply")

    with patch("app.services.ai_provider.get_provider", return_value=provider):
        response = client.post(
            f"/api/v1/memories/{memory['id']}/past-self-chat",
            headers=auth_headers,
            json={"message": "What did I need that day?"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conversation"]["mode"] == "past_self"
    assert data["conversation"]["anchor_diary_id"] == sample_diary["id"]
    assert data["assistant_message"]["content"].endswith("past self reply")


def test_admin_stats_include_memory_charts(client, admin_headers, auth_headers, test_user, sample_diary):
    create_memory(client, auth_headers, sample_diary, emotion_label="joy")

    response = client.get("/api/v1/admin/stats/charts", headers=admin_headers)

    assert response.status_code == 200
    stats = response.json()["data"]
    assert stats["total_memory_cards"] == 1
    assert stats["total_conversations"] >= 0
    assert stats["daily_new_memory_cards"]
    assert {"emotion": "joy", "count": 1} in stats["emotion_distribution"]
    assert stats["service_status"]["api"] == "healthy"


def test_delete_memory_card_deletes_associated_conversations(client, auth_headers, sample_diary, db_session):
    """Test that deleting a memory card also deletes associated past_self conversations and the diary."""
    from app.models.chat import Conversation
    from app.models.diary import MemoryCard, Diary

    # Create memory card
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]
    diary_id = sample_diary["id"]

    # Create a past_self conversation anchored to this diary
    conv_response = client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={
            "mode": "past_self",
            "anchor_diary_id": diary_id,
            "title": "Test Past Self Conversation"
        }
    )
    assert conv_response.status_code == 201
    conversation_id = conv_response.json()["data"]["conversation"]["id"]

    # Verify records exist before deletion
    conv_before = db_session.query(Conversation).filter_by(id=conversation_id).first()
    assert conv_before is not None
    assert conv_before.deleted_at is None

    diary_before = db_session.query(Diary).filter_by(id=diary_id).first()
    assert diary_before is not None
    assert diary_before.deleted_at is None

    # Delete the memory card
    delete_response = client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    # Verify memory card is soft-deleted
    memory_after = db_session.query(MemoryCard).filter_by(id=memory_id).first()
    assert memory_after is not None
    assert memory_after.deleted_at is not None

    # Verify associated conversation is also soft-deleted
    conv_after = db_session.query(Conversation).filter_by(id=conversation_id).first()
    assert conv_after is not None
    assert conv_after.deleted_at is not None

    # Verify associated diary is also soft-deleted
    diary_after = db_session.query(Diary).filter_by(id=diary_id).first()
    assert diary_after is not None
    assert diary_after.deleted_at is not None

    # Verify the response includes deletion indicators
    delete_data = delete_response.json()["data"]
    assert delete_data["deleted_conversations_count"] >= 1
    assert delete_data["diary_deleted"] is True

    # Verify diary count decreased in stats
    stats_response = client.get("/api/v1/stats/overview", headers=auth_headers)
    assert stats_response.status_code == 200
    stats = stats_response.json()["data"]
    assert stats["total_diaries"] == 0  # Diary was deleted
