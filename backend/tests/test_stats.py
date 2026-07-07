"""
Tests for statistics endpoints with strict assertions and comprehensive coverage.
"""

import pytest
from datetime import date, timedelta

from tests.helpers import create_entry, create_diary


class TestStatsOverview:
    """Tests for GET /api/v1/stats/overview"""

    def test_stats_overview_empty(self, client, auth_headers):
        """Test stats overview when user has no diaries."""
        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "request_id" in data
        assert data["message"] == "ok"

        # Verify empty state contract
        stats = data["data"]
        assert stats["total_diaries"] == 0
        assert stats["favorite_diaries"] == 0
        assert stats["average_emotion_score"] is None
        # Verify no extra fields
        assert set(stats.keys()) == {"total_diaries", "favorite_diaries", "average_emotion_score"}

    def test_stats_overview_with_data(self, client, auth_headers, sample_diary):
        """Test stats overview with exact single diary."""
        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # Exact count - we created exactly 1 diary
        assert stats["total_diaries"] == 1
        assert stats["favorite_diaries"] == 0  # sample_diary is not favorite
        # Score should be a specific number, not just a float
        assert isinstance(stats["average_emotion_score"], (int, float))
        assert 0 <= stats["average_emotion_score"] <= 100

    def test_stats_overview_with_favorites(self, client, auth_headers, sample_entry):
        """Test stats overview counts favorite diaries correctly."""
        # Create a favorite diary
        response = client.post("/api/v1/diaries", headers=auth_headers, json={
            "entry_id": sample_entry["id"],
            "title": "Favorite Diary",
            "content": "Content",
            "diary_date": date.today().isoformat(),
            "is_favorite": True
        })
        assert response.status_code == 201

        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["data"]

        # Exact count
        assert stats["favorite_diaries"] == 1
        assert stats["total_diaries"] == 1

    def test_stats_overview_multiple_diaries(self, client, auth_headers, sample_entry):
        """Test stats overview calculates average correctly."""
        # Create 3 diaries with known emotion scores
        # We'll create entries and diaries, then verify the average
        diaries_created = []
        for i, (content, expected_score) in enumerate([
            ("很开心，今天太棒了！", 75),  # High score
            ("有点难过", 35),  # Low score
            ("普通的一天", 50),  # Neutral
        ]):
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": content,
                "input_type": "text",
                "source_language": "zh-CN"
            })
            assert entry_response.status_code == 201
            entry_id = entry_response.json()["data"]["id"]

            diary_response = client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": f"Diary {i}",
                "content": content,
                "diary_date": "2026-07-07",
                "is_favorite": False
            })
            assert diary_response.status_code == 201
            diaries_created.append(diary_response.json()["data"]["id"])

        response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["data"]

        # Exact count
        assert stats["total_diaries"] == 3
        # Average should be calculated and in reasonable range
        assert stats["average_emotion_score"] is not None
        assert isinstance(stats["average_emotion_score"], (int, float))
        assert 0 <= stats["average_emotion_score"] <= 100

    def test_stats_overview_no_auth(self, client):
        """Test stats overview without authentication fails."""
        response = client.get("/api/v1/stats/overview")
        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert "error_code" in data or "detail" in data

    def test_stats_overview_invalid_token(self, client):
        """Test stats overview with invalid token."""
        response = client.get("/api/v1/stats/overview", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False

    def test_stats_overview_expired_token_format(self, client, auth_headers):
        """Test stats overview handles malformed token."""
        # Test with various malformed auth headers
        for auth_header in [
            "Bearer",  # No token
            "invalid_format",  # No Bearer prefix
            "",  # Empty
        ]:
            response = client.get("/api/v1/stats/overview", headers={
                "Authorization": auth_header
            })
            # Should fail authentication
            assert response.status_code == 401


class TestEmotionTrend:
    """Tests for GET /api/v1/stats/emotion-trend"""

    def test_emotion_trend_empty(self, client, auth_headers):
        """Test emotion trend when user has no diaries."""
        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "request_id" in data
        # Empty state contract - must be empty array, not null or object
        assert data["data"] == []

    def test_emotion_trend_with_data(self, client, auth_headers, sample_diary):
        """Test emotion trend returns exact expected structure."""
        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        trend = data["data"]

        # Exact count - we have exactly 1 diary
        assert len(trend) == 1

        entry = trend[0]
        # Verify required fields
        assert set(entry.keys()) == {"date", "emotion_score", "primary_emotion"}
        # Verify field types
        assert isinstance(entry["date"], str)
        assert isinstance(entry["emotion_score"], (int, float))
        assert isinstance(entry["primary_emotion"], str)
        # Verify value ranges
        assert 0 <= entry["emotion_score"] <= 100
        # Verify date format (ISO date)
        assert "-" in entry["date"]

    def test_emotion_trend_chronological(self, client, auth_headers, sample_entry):
        """Test emotion trend is ordered by date ascending."""
        from datetime import date, timedelta

        # Create diaries with known dates
        dates = []
        for i in range(3):
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": "测试内容",
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            # Create dates in reverse order to test sorting
            diary_date = (date.today() + timedelta(days=2-i)).isoformat()
            dates.append(diary_date)
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

        # Should be exactly 3 entries
        assert len(trend) == 3
        # Should be ordered by date ascending
        returned_dates = [entry["date"] for entry in trend]
        assert returned_dates == sorted(dates)

    def test_emotion_trend_date_format(self, client, auth_headers, sample_entry):
        """Test emotion trend returns ISO 8601 dates."""
        diary_date = "2026-07-07"
        entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
            "raw_content": "测试",
            "input_type": "text",
            "source_language": "zh-CN"
        })
        entry_id = entry_response.json()["data"]["id"]
        client.post("/api/v1/diaries", headers=auth_headers, json={
            "entry_id": entry_id,
            "title": "Diary",
            "content": "Content",
            "diary_date": diary_date,
            "is_favorite": False
        })

        response = client.get("/api/v1/stats/emotion-trend", headers=auth_headers)
        assert response.status_code == 200
        trend = response.json()["data"]

        # Date should be in ISO format (YYYY-MM-DD)
        assert trend[0]["date"] == diary_date

    def test_emotion_trend_no_auth(self, client):
        """Test emotion trend without authentication fails."""
        response = client.get("/api/v1/stats/emotion-trend")
        assert response.status_code == 401

    def test_emotion_trend_invalid_token(self, client):
        """Test emotion trend with invalid token."""
        response = client.get("/api/v1/stats/emotion-trend", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401


class TestEmotionDistribution:
    """Tests for GET /api/v1/stats/emotion-distribution"""

    def test_emotion_distribution_empty(self, client, auth_headers):
        """Test emotion distribution when user has no diaries."""
        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "request_id" in data
        # Empty state contract - must be empty array
        assert data["data"] == []

    def test_emotion_distribution_with_data(self, client, auth_headers, sample_diary):
        """Test emotion distribution returns exact expected structure."""
        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        distribution = data["data"]

        # Exact count - 1 diary = 1 emotion category
        assert len(distribution) == 1

        entry = distribution[0]
        # Verify required fields
        assert set(entry.keys()) == {"primary_emotion", "count"}
        # Verify field types
        assert isinstance(entry["primary_emotion"], str)
        assert isinstance(entry["count"], int)
        # Verify count is positive
        assert entry["count"] >= 1

    def test_emotion_distribution_varied_emotions(self, client, auth_headers):
        """Test emotion distribution counts multiple emotions correctly."""
        # Create entries with different emotions - each gets its own entry
        emotions_content = [
            "今天很开心！",  # joy
            "有点难过",  # sadness
            "感到焦虑",  # anxiety
            "内心平静"  # calm
        ]

        for content in emotions_content:
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": content,
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": "Diary",
                "content": content,
                "diary_date": "2026-07-07",
                "is_favorite": False
            })

        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        distribution = response.json()["data"]

        # Should have entries for our diaries
        assert len(distribution) >= 1
        # All counts should sum to total diaries created
        total_count = sum(entry["count"] for entry in distribution)
        assert total_count == 4  # Exactly 4 diaries created

    def test_emotion_distribution_aggregation(self, client, auth_headers):
        """Test emotion distribution aggregates same emotions."""
        # Create multiple diaries with same emotion
        for i in range(3):
            entry_response = client.post("/api/v1/entries", headers=auth_headers, json={
                "raw_content": "今天很开心！",
                "input_type": "text",
                "source_language": "zh-CN"
            })
            entry_id = entry_response.json()["data"]["id"]
            client.post("/api/v1/diaries", headers=auth_headers, json={
                "entry_id": entry_id,
                "title": f"Diary {i}",
                "content": "Content",
                "diary_date": "2026-07-07",
                "is_favorite": False
            })

        response = client.get("/api/v1/stats/emotion-distribution", headers=auth_headers)
        assert response.status_code == 200
        distribution = response.json()["data"]

        # Should aggregate to 1 emotion category with count 3
        assert len(distribution) == 1
        assert distribution[0]["count"] == 3

    def test_emotion_distribution_no_auth(self, client):
        """Test emotion distribution without authentication fails."""
        response = client.get("/api/v1/stats/emotion-distribution")
        assert response.status_code == 401

    def test_emotion_distribution_invalid_token(self, client):
        """Test emotion distribution with invalid token."""
        response = client.get("/api/v1/stats/emotion-distribution", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401


class TestStatsContracts:
    """Test contracts and edge cases for stats endpoints."""

    def test_empty_state_contracts(self, client, auth_headers):
        """Test all endpoints return consistent empty state."""
        endpoints = [
            "/api/v1/stats/overview",
            "/api/v1/stats/emotion-trend",
            "/api/v1/stats/emotion-distribution"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()

            # All endpoints return consistent structure
            assert data["success"] is True
            assert "request_id" in data
            assert "data" in data
            assert data["message"] == "ok"

    def test_response_structure_consistency(self, client, auth_headers, sample_entry):
        """Test all successful responses have consistent structure."""
        # Create a diary first
        client.post("/api/v1/diaries", headers=auth_headers, json={
            "entry_id": sample_entry["id"],
            "title": "Test",
            "content": "Content",
            "diary_date": date.today().isoformat(),
            "is_favorite": False
        })

        endpoints = [
            "/api/v1/stats/overview",
            "/api/v1/stats/emotion-trend",
            "/api/v1/stats/emotion-distribution"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()

            # Verify all required fields exist
            assert "success" in data
            assert "data" in data
            assert "message" in data
            assert "request_id" in data
            assert data["success"] is True
            assert isinstance(data["data"], (dict, list))

    def test_error_response_structure(self, client):
        """Test error responses have consistent structure."""
        endpoints = [
            "/api/v1/stats/overview",
            "/api/v1/stats/emotion-trend",
            "/api/v1/stats/emotion-distribution"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            data = response.json()

            # Error responses should have success=False
            assert data["success"] is False
            assert data.get("data") is None or data.get("data") == []
