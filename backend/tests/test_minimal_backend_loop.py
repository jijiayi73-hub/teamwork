"""
Minimal backend loop tests - updated to use pytest fixtures.
"""

from datetime import date

import pytest


def register(client, email="user@example.com", role="user"):
    """Helper to register a user and return token."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": email.split("@")[0], "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201
    return response.json()["data"]["access_token"]


def test_health_and_user_diary_stats_loop(client):
    """Test the complete minimal backend loop."""
    # Use unique email to avoid conflicts with parallel tests
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    token = register(client, f"user_{unique_id}@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    entry_response = client.post(
        "/api/v1/entries",
        json={"raw_content": "今天考试压力很大，有点焦虑，但是写下来以后平静了一点。"},
        headers=headers,
    )
    assert entry_response.status_code == 201
    entry = entry_response.json()["data"]
    assert entry["status"] == "analyzed"
    assert entry["analysis"]["primary_emotion"] in {"anxiety", "sadness", "calm", "neutral"}

    diary_response = client.post(
        "/api/v1/diaries",
        json={
            "entry_id": entry["id"],
            "title": entry["draft_title"],
            "content": entry["draft_content"],
            "diary_date": date.today().isoformat(),
            "is_favorite": True,
        },
        headers=headers,
    )
    assert diary_response.status_code == 201
    diary = diary_response.json()["data"]
    assert diary["entry_id"] == entry["id"]

    list_response = client.get("/api/v1/diaries", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    overview_response = client.get("/api/v1/stats/overview", headers=headers)
    assert overview_response.status_code == 200
    assert overview_response.json()["data"]["total_diaries"] == 1


def test_admin_stats_are_role_protected(client):
    """Test that admin endpoints are protected."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    user_token = register(client, f"normal_{unique_id}@example.com")
    forbidden = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden.status_code == 403

    admin_token = register(client, f"admin_{unique_id}@example.com", role="admin")
    response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    # The admin user should exist in the stats
    assert response.json()["data"]["total_users"] >= 1
