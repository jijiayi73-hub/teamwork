"""
Tests for statistics endpoints.
"""

import pytest

from tests.helpers import create_entry, create_diary


class TestStatsOverview:
    """Tests for GET /api/v1/stats/overview"""

    def test_stats_overview_empty(self, client, auth_headers):
        """Test stats overview when user has no diaries."""
        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        stats = data["data"]
        assert stats["total_diaries"] == 0
        assert stats["favorite_diaries"] == 0
        assert stats["average_emotion_score"] is None

    def test_stats_overview_with_data(self, client, auth_headers, sample_diary):
        """Test stats overview with user data."""
        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        stats = data["data"]
        assert stats["total_diaries"] >= 1
        assert isinstance(stats["average_emotion_score"], (int, float))

    def test_stats_overview_with_favorites(self, client, auth_headers, sample_entry):
        """Test stats overview counts favorite diaries."""
        # Create a favorite diary
        from datetime import date
        client.post("/api/v1/diaries", headers=auth_headers, json={
            "entry_id": sample_entry["id"],
            "title": "Favorite Diary",
            "content": "Content",
            "diary_date": date.today().isoformat(),
            "is_favorite": True
        })

        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["data"]
        assert stats["favorite_diaries"] >= 1

    def test_stats_overview_multiple_diaries(self, client, auth_headers, sample_entry):
        """Test stats overview with multiple diaries."""
        # Create multiple diaries with different emotion scores
        for content in ["开心", "难过", "平静"]:
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": content,
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": f"Diary for {content}",
                "content": "Content",
                "diary_date": "2026-07-07",
                "is_favorite": False
            })

        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["data"]
        assert stats["total_diaries"] >= 3
        # Average should be calculated
        assert stats["average_emotion_score"] is not None

    def test_stats_overview_no_auth(self, client):
        """Test stats overview without authentication fails."""
        response = client.get("/api/v1/stats/overview")
        assert response.status_code == 401


class TestEmotionTrend:
    """Tests for GET /api/v1/stats/emotion-trend"""

    def test_emotion_trend_empty(self, client, auth_headers):
        """Test emotion trend when user has no diaries."""
        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_emotion_trend_with_data(self, client, auth_headers, sample_diary):
        """Test emotion trend with user data."""
        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        trend = data["data"]
        assert len(trend) >= 1
        entry = trend[0]
        assert "date" in entry
        assert "emotion_score" in entry
        assert "primary_emotion" in entry

    def test_emotion_trend_chronological(self, client, auth_headers, sample_entry):
        """Test emotion trend is ordered by date."""
        from datetime import date, timedelta

        # Create diaries with different dates
        for i in range(3):
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": "测试内容",
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            diary_date = (date.today() + timedelta(days=i)).isoformat()
            client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": f"Diary {i}",
                "content": "Content",
                "diary_date": diary_date,
                "is_favorite": False
            })

        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        trend = response.json()["data"]
        # Should be ordered by date
        dates = [entry["date"] for entry in trend]
        assert dates == sorted(dates)

    def test_emotion_trend_no_auth(self, client):
        """Test emotion trend without authentication fails."""
        response = client.get("/api/v1/stats/emotion-trend")
        assert response.status_code == 401


class TestEmotionDistribution:
    """Tests for GET /api/v1/stats/emotion-distribution"""

    def test_emotion_distribution_empty(self, client, auth_headers):
        """Test emotion distribution when user has no diaries."""
        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_emotion_distribution_with_data(self, client, auth_headers, sample_diary):
        """Test emotion distribution with user data."""
        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        distribution = data["data"]
        assert len(distribution) >= 1
        entry = distribution[0]
        assert "primary_emotion" in entry
        assert "count" in entry

    def test_emotion_distribution_varied_emotions(self, client, auth_headers):
        """Test emotion distribution with various emotions."""
        # Create entries with different emotions
        emotions_content = {
            "joy": "今天很开心！",
            "sadness": "有点难过",
            "anxiety": "感到焦虑",
            "calm": "内心平静"
        }

        for content in emotions_content.values():
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": content,
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": "Diary",
                "content": "Content",
                "diary_date": "2026-07-07",
                "is_favorite": False
            })

        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        distribution = response.json()["data"]
        # Should have multiple emotions
        assert len(distribution) >= 1
        # All counts should sum to total diaries
        total_count = sum(entry["count"] for entry in distribution)
        assert total_count >= 4

    def test_emotion_distribution_no_auth(self, client):
        """Test emotion distribution without authentication fails."""
        response = client.get("/api/v1/stats/emotion-distribution")
        assert response.status_code == 401
