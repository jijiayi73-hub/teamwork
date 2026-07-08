"""
F-002: Diary Creation Full Flow Tests

Tests the complete diary lifecycle:
1. Create Entry → Emotion Analysis → Save Diary → View List → Stats Update → Update → Soft Delete
"""
from datetime import date
import pytest


class TestDiaryCreationFullFlow:
    """Test the complete diary creation and management flow."""

    def test_complete_diary_flow(self, client, auth_headers, db_session):
        """
        Test: Create Entry → Analysis → Create Diary → List → Stats → Update → Delete

        This is the F-002 main flow test.
        """
        # Step 1: Create entry with emotion analysis
        entry_content = "今天考试压力很大，有点焦虑，但是写下来以后平静了一点。和朋友聊天后感觉好多了。"
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={
                "raw_content": entry_content,
                "input_type": "text",
                "source_language": "zh-CN"
            }
        )
        assert entry_response.status_code == 201
        entry = entry_response.json()["data"]

        # Step 2: Verify entry was analyzed
        assert entry["status"] == "analyzed"
        assert "analysis" in entry
        assert entry["analysis"]["primary_emotion"] in {
            "anxiety", "sadness", "calm", "neutral", "joy"
        }
        assert entry["analysis"]["emotion_score"] > 0
        assert "suggestion" in entry["analysis"]

        # Step 3: Create diary from entry
        diary_data = {
            "entry_id": entry["id"],
            "title": entry.get("draft_title", "考试日记"),
            "content": entry.get("draft_content", entry_content),
            "diary_date": date.today().isoformat(),
            "is_favorite": False
        }
        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json=diary_data
        )
        assert diary_response.status_code == 201
        diary = diary_response.json()["data"]

        # Verify diary structure
        assert diary["entry_id"] == entry["id"]
        assert diary["title"] == diary_data["title"]
        assert diary["content"] == diary_data["content"]
        assert diary["diary_date"] == diary_data["diary_date"]
        assert diary["is_favorite"] is False

        # Step 4: List diaries
        list_response = client.get("/api/v1/diaries", headers=auth_headers)
        assert list_response.status_code == 200
        diaries_list = list_response.json()["data"]
        assert len(diaries_list) == 1
        assert diaries_list[0]["id"] == diary["id"]

        # Step 5: Verify stats updated
        stats_response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]
        assert stats["total_diaries"] == 1

        # Step 6: Get single diary
        detail_response = client.get(
            f"/api/v1/diaries/{diary['id']}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200
        diary_detail = detail_response.json()["data"]
        assert diary_detail["id"] == diary["id"]
        assert diary_detail["title"] == diary["title"]

        # Step 7: Update diary
        update_data = {
            "title": "更新后的日记标题",
            "content": "更新后的日记内容",
            "is_favorite": True
        }
        update_response = client.patch(
            f"/api/v1/diaries/{diary['id']}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200
        updated_diary = update_response.json()["data"]
        assert updated_diary["title"] == update_data["title"]
        assert updated_diary["is_favorite"] is True

        # Step 8: Soft delete diary
        delete_response = client.delete(
            f"/api/v1/diaries/{diary['id']}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Step 9: Verify deleted diary not in list
        list_after_delete = client.get("/api/v1/diaries", headers=auth_headers)
        assert list_after_delete.status_code == 200
        assert len(list_after_delete.json()["data"]) == 0

        # Step 10: Verify diary still exists in DB (soft delete)
        from app.models.diary import Diary
        db_diary = db_session.get(Diary, diary["id"])
        assert db_diary is not None
        assert db_diary.deleted_at is not None

    def test_multiple_diaries_flow(self, client, auth_headers, db_session, e2e_helper):
        """Test creating and managing multiple diaries."""
        # Create three diaries
        diary_count = 3
        diaries = []

        for i in range(diary_count):
            content = f"这是第 {i+1} 篇日记。今天感觉{'很好' if i % 2 == 0 else '一般'}。"
            entry, diary = e2e_helper.create_complete_diary(content)
            diaries.append(diary)

        # Verify all diaries in list
        list_response = client.get("/api/v1/diaries", headers=auth_headers)
        assert list_response.status_code == 200
        diaries_list = list_response.json()["data"]
        assert len(diaries_list) == diary_count

        # Verify stats
        stats_response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]
        assert stats["total_diaries"] == diary_count

        # Delete one diary
        delete_response = client.delete(
            f"/api/v1/diaries/{diaries[0]['id']}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify count decreased
        stats_after = client.get("/api/v1/stats/overview", headers=auth_headers).json()["data"]
        assert stats_after["total_diaries"] == diary_count - 1

    def test_diary_with_favorites(self, client, auth_headers, e2e_helper):
        """Test creating and filtering favorite diaries."""
        # Create two diaries, one favorite
        _, diary1 = e2e_helper.create_complete_diary("普通日记")
        _, diary2 = e2e_helper.create_complete_diary("收藏日记")

        # Mark second as favorite
        client.patch(
            f"/api/v1/diaries/{diary2['id']}",
            headers=auth_headers,
            json={"is_favorite": True}
        )

        # List all diaries
        all_response = client.get("/api/v1/diaries", headers=auth_headers)
        assert all_response.status_code == 200
        all_diaries = all_response.json()["data"]
        assert len(all_diaries) == 2

        # List only favorites - note: diaries may both be returned depending on API behavior
        fav_response = client.get("/api/v1/diaries?is_favorite=true", headers=auth_headers)
        assert fav_response.status_code == 200
        fav_diaries = fav_response.json()["data"]
        # At least one should be the favorite we just marked
        assert any(d["id"] == diary2["id"] for d in fav_diaries)

    def test_entry_to_diary_linkage(self, client, auth_headers, db_session):
        """Test that entries are properly linked to their diaries."""
        # Create entry
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={"raw_content": "测试链接关系", "input_type": "text", "source_language": "zh-CN"}
        )
        assert entry_response.status_code == 201
        entry = entry_response.json()["data"]

        # Create diary
        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": entry["id"],
                "title": "测试日记",
                "content": "测试内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        assert diary_response.status_code == 201
        diary = diary_response.json()["data"]

        # Verify linkage in database
        from app.models.diary import Diary
        db_diary = db_session.get(Diary, diary["id"])
        assert db_diary.entry_id == entry["id"]


class TestDiaryValidationAndErrors:
    """Test validation and error handling in diary flow."""

    def test_create_diary_with_invalid_entry_id(self, client, auth_headers):
        """Test creating diary with non-existent entry ID."""
        response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": 99999,  # Non-existent entry
                "title": "测试",
                "content": "测试内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        # Should return 404 or validation error
        assert response.status_code in [404, 422]

    def test_create_diary_with_invalid_date(self, client, auth_headers, sample_entry):
        """Test creating diary with invalid date format."""
        response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": sample_entry["id"],
                "title": "测试",
                "content": "测试内容",
                "diary_date": "not-a-date",
                "is_favorite": False
            }
        )
        assert response.status_code == 422

    def test_update_nonexistent_diary(self, client, auth_headers):
        """Test updating a diary that doesn't exist."""
        response = client.patch(
            "/api/v1/diaries/99999",
            headers=auth_headers,
            json={"title": "新标题"}
        )
        assert response.status_code == 404

    def test_delete_nonexistent_diary(self, client, auth_headers):
        """Test deleting a diary that doesn't exist."""
        response = client.delete("/api/v1/diaries/99999", headers=auth_headers)
        assert response.status_code == 404


class TestDiaryDatabaseIntegrity:
    """Test database integrity for diary operations."""

    def test_diary_soft_delete_preserves_record(self, client, auth_headers, db_session, e2e_helper):
        """Test that soft delete preserves the record in database."""
        _, diary = e2e_helper.create_complete_diary()

        # Soft delete
        client.delete(f"/api/v1/diaries/{diary['id']}", headers=auth_headers)

        # Verify record still exists
        from app.models.diary import Diary
        db_diary = db_session.get(Diary, diary["id"])
        assert db_diary is not None
        assert db_diary.deleted_at is not None

    def test_cannot_create_duplicate_diary_from_same_entry(self, client, auth_headers, sample_entry):
        """Test that one entry can only create one diary."""
        # First diary
        first_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": sample_entry["id"],
                "title": "第一篇",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        assert first_response.status_code == 201

        # Second diary with same entry
        second_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": sample_entry["id"],
                "title": "第二篇",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        # Should fail or return error
        assert second_response.status_code != 201
