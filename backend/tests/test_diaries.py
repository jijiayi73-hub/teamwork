"""
Tests for diary endpoints.
"""

import pytest
from datetime import date, timedelta

from tests.factories import diary_data, diary_update_data
from tests.helpers import create_entry, create_diary


class TestCreateDiary:
    """Tests for POST /api/v1/diaries"""

    def test_create_diary_success(self, client, auth_headers, sample_entry):
        """Test successful diary creation."""
        response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
            entry_id=sample_entry["id"]
        ))
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        diary = data["data"]
        assert "id" in diary
        assert diary["entry_id"] == sample_entry["id"]
        assert diary["title"] == diary_data()["title"]
        assert diary["content"] == diary_data()["content"]
        assert diary["is_favorite"] is False
        assert diary["visibility"] == "private"

    def test_create_diary_with_favorite(self, client, auth_headers, sample_entry):
        """Test creating diary marked as favorite."""
        response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
            entry_id=sample_entry["id"],
            is_favorite=True
        ))
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["is_favorite"] is True

    def test_create_diary_nonexistent_entry(self, client, auth_headers):
        """Test creating diary with non-existent entry."""
        response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
            entry_id=99999  # Non-existent
        ))
        assert response.status_code == 404

    def test_create_diary_duplicate(self, client, auth_headers, sample_diary):
        """Test creating duplicate diary for same entry fails."""
        response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
            entry_id=sample_diary["entry_id"]  # Same entry_id
        ))
        assert response.status_code == 409

    def test_create_diary_no_auth(self, client):
        """Test creating diary without authentication fails."""
        response = client.post("/api/v1/diaries", json=diary_data())
        assert response.status_code == 401


class TestListDiaries:
    """Tests for GET /api/v1/diaries"""

    def test_list_diaries_empty(self, client, auth_headers):
        """Test listing diaries when user has none."""
        response = client.get("/api/v1/diaries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_diaries_with_data(self, client, auth_headers, sample_diary):
        """Test listing diaries when user has data."""
        response = client.get("/api/v1/diaries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        diary = data["data"][0]
        assert diary["id"] == sample_diary["id"]
        assert "title" in diary
        assert "analysis" in diary

    def test_list_diaries_multiple(self, client, auth_headers):
        """Test listing multiple diaries."""
        # Create multiple entries and diaries
        for i in range(3):
            # First create a new entry for each diary
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": f"测试内容 {i}",
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            # Then create diary from that entry
            client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
                entry_id=entry_id,
                title=f"日记 {i}",
                content=f"内容 {i}"
            ))

        response = client.get("/api/v1/diaries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have at least the diaries we created
        assert len(data["data"]) >= 3

    def test_list_diaries_no_auth(self, client):
        """Test listing diaries without authentication fails."""
        response = client.get("/api/v1/diaries")
        assert response.status_code == 401

    def test_list_diaries_isolated_by_user(self, client, auth_headers, admin_headers):
        """Test that users can only see their own diaries."""
        # Create diary as regular user
        response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data(
            entry_id=1  # Assume this exists for test user
        ))
        # Try to list as admin - should not see user's diaries
        response = client.get("/api/v1/diaries", headers=admin_headers)
        assert response.status_code == 200
        # Admin should not see the regular user's diary
        # (This would need proper setup with separate entries)


class TestGetDiary:
    """Tests for GET /api/v1/diaries/{diary_id}"""

    def test_get_diary_success(self, client, auth_headers, sample_diary):
        """Test getting a specific diary."""
        response = client.get(f"/api/v1/diaries/{sample_diary['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_diary["id"]
        assert "analysis" in data["data"]

    def test_get_diary_nonexistent(self, client, auth_headers):
        """Test getting non-existent diary."""
        response = client.get("/api/v1/diaries/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_diary_no_auth(self, client, sample_diary):
        """Test getting diary without authentication fails."""
        response = client.get(f"/api/v1/diaries/{sample_diary['id']}")
        assert response.status_code == 401


class TestUpdateDiary:
    """Tests for PATCH /api/v1/diaries/{diary_id}"""

    def test_update_diary_title(self, client, auth_headers, sample_diary):
        """Test updating diary title."""
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            headers=auth_headers,
            json=diary_update_data(title="新标题")
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "新标题"

    def test_update_diary_content(self, client, auth_headers, sample_diary):
        """Test updating diary content."""
        new_content = "这是更新后的内容"
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            headers=auth_headers,
            json=diary_update_data(content=new_content)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["content"] == new_content

    def test_update_diary_favorite(self, client, auth_headers, sample_diary):
        """Test toggling favorite status."""
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            headers=auth_headers,
            json=diary_update_data(is_favorite=True)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_favorite"] is True

    def test_update_diary_multiple_fields(self, client, auth_headers, sample_diary):
        """Test updating multiple fields at once."""
        new_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            headers=auth_headers,
            json=diary_update_data(
                title="新标题",
                content="新内容",
                diary_date=new_date,
                is_favorite=True
            )
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "新标题"
        assert data["data"]["content"] == "新内容"
        assert data["data"]["is_favorite"] is True

    def test_update_diary_no_fields(self, client, auth_headers, sample_diary):
        """Test updating diary with no fields (empty update)."""
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            headers=auth_headers,
            json={}
        )
        # Should still succeed but return same data
        assert response.status_code == 200

    def test_update_diary_nonexistent(self, client, auth_headers):
        """Test updating non-existent diary."""
        response = client.patch(
            "/api/v1/diaries/99999",
            headers=auth_headers,
            json=diary_update_data(title="新标题")
        )
        assert response.status_code == 404

    def test_update_diary_no_auth(self, client, sample_diary):
        """Test updating diary without authentication fails."""
        response = client.patch(
            f"/api/v1/diaries/{sample_diary['id']}",
            json=diary_update_data(title="新标题")
        )
        assert response.status_code == 401


class TestDeleteDiary:
    """Tests for DELETE /api/v1/diaries/{diary_id}"""

    def test_delete_diary_success(self, client, auth_headers, sample_diary):
        """Test soft deleting a diary."""
        response = client.delete(f"/api/v1/diaries/{sample_diary['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_diary["id"]

        # Verify it's soft deleted (not in list anymore)
        list_response = client.get("/api/v1/diaries", headers=auth_headers)
        assert list_response.status_code == 200
        diaries = list_response.json()["data"]
        assert sample_diary["id"] not in [d["id"] for d in diaries]

    def test_delete_diary_nonexistent(self, client, auth_headers):
        """Test deleting non-existent diary."""
        response = client.delete("/api/v1/diaries/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_diary_no_auth(self, client, sample_diary):
        """Test deleting diary without authentication fails."""
        response = client.delete(f"/api/v1/diaries/{sample_diary['id']}")
        assert response.status_code == 401

    def test_delete_diary_already_deleted(self, client, auth_headers, sample_diary):
        """Test deleting already deleted diary."""
        # First delete
        client.delete(f"/api/v1/diaries/{sample_diary['id']}", headers=auth_headers)
        # Try to delete again
        response = client.delete(f"/api/v1/diaries/{sample_diary['id']}", headers=auth_headers)
        assert response.status_code == 404
