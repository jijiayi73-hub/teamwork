"""Tests for trash/recycle bin functionality."""

import pytest


def create_memory(client, auth_headers, sample_diary, **overrides):
    """Helper to create a memory card."""
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


def test_list_empty_trash(client, auth_headers):
    """Test listing trash when it's empty."""
    response = client.get("/api/v1/trash", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


def test_list_trash_with_deleted_item(client, auth_headers, sample_diary):
    """Test listing trash after deleting a memory card."""
    from app.models.chat import Conversation

    # Create memory card
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]
    diary_id = sample_diary["id"]

    # Create a conversation
    conv_response = client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={
            "mode": "past_self",
            "anchor_diary_id": diary_id,
            "title": "Test Conversation"
        }
    )
    assert conv_response.status_code == 201

    # Delete the memory card
    delete_response = client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    # List trash
    trash_response = client.get("/api/v1/trash", headers=auth_headers)
    assert trash_response.status_code == 200
    data = trash_response.json()["data"]
    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["id"] == memory_id
    assert item["diary_id"] == diary_id
    assert item["title"] == sample_diary["title"]
    assert item["deleted_conversations_count"] == 1


def test_restore_deleted_item(client, auth_headers, sample_diary, db_session):
    """Test restoring a deleted memory card."""
    from app.models.diary import MemoryCard, Diary

    # Create and delete memory card
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]
    diary_id = sample_diary["id"]

    client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # Verify deleted state
    memory = db_session.query(MemoryCard).filter_by(id=memory_id).first()
    assert memory.deleted_at is not None

    diary = db_session.query(Diary).filter_by(id=diary_id).first()
    assert diary.deleted_at is not None

    # Restore the item
    restore_response = client.post(
        f"/api/v1/trash/{memory_id}/restore",
        headers=auth_headers
    )
    assert restore_response.status_code == 200
    restore_data = restore_response.json()["data"]
    assert restore_data["id"] == memory_id
    assert restore_data["diary_restored"] is True
    assert restore_data["conversations_restored"] >= 0

    # Verify restored state
    db_session.refresh(memory)
    db_session.refresh(diary)
    assert memory.deleted_at is None
    assert diary.deleted_at is None

    # Verify it's back in the active list
    list_response = client.get("/api/v1/memories", headers=auth_headers)
    assert list_response.status_code == 200
    memories = list_response.json()["data"]
    assert len(memories) == 1
    assert memories[0]["id"] == memory_id


def test_restore_nonexistent_item(client, auth_headers):
    """Test restoring an item that doesn't exist."""
    response = client.post("/api/v1/trash/999/restore", headers=auth_headers)
    assert response.status_code == 404


def test_permanent_delete_item(client, auth_headers, sample_diary, db_session):
    """Test permanently deleting an item from trash."""
    from app.models.diary import MemoryCard, Diary

    # Create and delete memory card
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]

    client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # Permanently delete from trash
    perm_delete_response = client.delete(
        f"/api/v1/trash/{memory_id}",
        headers=auth_headers
    )
    assert perm_delete_response.status_code == 200
    assert perm_delete_response.json()["data"]["id"] == memory_id

    # Verify it's gone
    memory = db_session.query(MemoryCard).filter_by(id=memory_id).first()
    assert memory is None

    diary = db_session.query(Diary).filter_by(id=sample_diary["id"]).first()
    assert diary is None


def test_batch_restore(client, auth_headers, db_session):
    """Test batch restoring multiple items."""
    from app.models.diary import MemoryCard

    # Create multiple diaries and memories
    memory_ids = []
    for i in range(3):
        # Create entry for each memory
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={
                "raw_content": f"Test entry {i}",
                "input_type": "text",
                "source_language": "zh-CN"
            }
        )
        entry_id = entry_response.json()["data"]["id"]

        # Create diary
        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": entry_id,
                "title": f"Test Diary {i}",
                "content": f"Test content {i}",
                "diary_date": "2026-01-01"
            }
        )
        diary_id = diary_response.json()["data"]["id"]

        # Create memory
        memory_response = client.post(
            "/api/v1/memories",
            headers=auth_headers,
            json={
                "diary_id": diary_id,
                "cover_image_url": "/uploads/demo.png",
                "emotion_label": f"emotion_{i}",
                "emotion_color": f"#color{i}",
                "keywords": ["test"],
                "conversation_summary": "test summary"
            }
        )
        memory_ids.append(memory_response.json()["data"]["id"])

    # Delete all
    for memory_id in memory_ids:
        client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # Batch restore
    batch_response = client.post(
        "/api/v1/trash/batch/restore",
        headers=auth_headers,
        json={"memory_ids": memory_ids}
    )
    assert batch_response.status_code == 200
    batch_data = batch_response.json()["data"]
    assert batch_data["restored_count"] == 3
    assert batch_data["skipped_count"] == 0

    # Verify all are restored
    memories = (
        db_session.query(MemoryCard)
        .filter(MemoryCard.id.in_(memory_ids))
        .all()
    )
    assert len(memories) == 3
    for memory in memories:
        assert memory.deleted_at is None


def test_batch_permanent_delete(client, auth_headers, db_session):
    """Test batch permanent delete."""
    from app.models.diary import MemoryCard

    # Create multiple diaries and memories
    memory_ids = []
    for i in range(3):
        # Create entry for each memory
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={
                "raw_content": f"Test entry {i}",
                "input_type": "text",
                "source_language": "zh-CN"
            }
        )
        entry_id = entry_response.json()["data"]["id"]

        # Create diary
        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": entry_id,
                "title": f"Test Diary {i}",
                "content": f"Test content {i}",
                "diary_date": "2026-01-01"
            }
        )
        diary_id = diary_response.json()["data"]["id"]

        # Create memory
        memory_response = client.post(
            "/api/v1/memories",
            headers=auth_headers,
            json={
                "diary_id": diary_id,
                "cover_image_url": "/uploads/demo.png",
                "emotion_label": f"emotion_{i}",
                "emotion_color": f"#color{i}",
                "keywords": ["test"],
                "conversation_summary": "test summary"
            }
        )
        memory_ids.append(memory_response.json()["data"]["id"])

    # Delete all
    for memory_id in memory_ids:
        client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # Batch permanent delete (delete only first 2)
    import json
    batch_response = client.request(
        "DELETE",
        "/api/v1/trash/batch",
        headers=auth_headers,
        content=json.dumps({"memory_ids": memory_ids[:2]}).encode()
    )
    assert batch_response.status_code == 200
    batch_data = batch_response.json()["data"]
    assert batch_data["deleted_count"] == 2
    assert batch_data["skipped_count"] == 0

    # Verify first 2 are gone, third still exists
    memories = (
        db_session.query(MemoryCard)
        .filter(MemoryCard.id.in_(memory_ids))
        .all()
    )
    assert len(memories) == 1
    assert memories[0].id == memory_ids[2]


def test_empty_trash(client, auth_headers, db_session):
    """Test emptying all trash."""
    from app.models.diary import MemoryCard

    # Create and delete multiple memories
    for i in range(3):
        # Create entry for each memory
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={
                "raw_content": f"Test entry {i}",
                "input_type": "text",
                "source_language": "zh-CN"
            }
        )
        entry_id = entry_response.json()["data"]["id"]

        # Create diary
        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": entry_id,
                "title": f"Test Diary {i}",
                "content": f"Test content {i}",
                "diary_date": "2026-01-01"
            }
        )
        diary_id = diary_response.json()["data"]["id"]

        # Create memory
        memory_response = client.post(
            "/api/v1/memories",
            headers=auth_headers,
            json={
                "diary_id": diary_id,
                "cover_image_url": "/uploads/demo.png",
                "emotion_label": f"emotion_{i}",
                "emotion_color": f"#color{i}",
                "keywords": ["test"],
                "conversation_summary": "test summary"
            }
        )
        memory_id = memory_response.json()["data"]["id"]
        client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # Verify trash has 3 items
    trash_response = client.get("/api/v1/trash", headers=auth_headers)
    assert trash_response.json()["data"]["total"] == 3

    # Empty trash
    empty_response = client.delete("/api/v1/trash/all", headers=auth_headers)
    assert empty_response.status_code == 200
    assert empty_response.json()["data"]["deleted_count"] == 3

    # Verify trash is empty
    trash_response = client.get("/api/v1/trash", headers=auth_headers)
    assert trash_response.json()["data"]["total"] == 0

    # Verify no memories exist for this user
    memories = db_session.query(MemoryCard).filter(
        MemoryCard.user_id == 1
    ).all()
    assert len(memories) == 0


def test_trash_isolated_by_user(client, auth_headers, admin_headers, sample_diary):
    """Test that users can only see their own trash."""
    # Create and delete memory as user
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]
    client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)

    # User can see it in trash
    user_trash = client.get("/api/v1/trash", headers=auth_headers)
    assert user_trash.json()["data"]["total"] == 1

    # Admin cannot see user's trash
    admin_trash = client.get("/api/v1/trash", headers=admin_headers)
    assert admin_trash.json()["data"]["total"] == 0
