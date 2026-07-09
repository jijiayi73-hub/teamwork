"""
Tests for entry endpoints.
"""

import pytest

from tests.factories import (
    entry_data,
    POSITIVE_CONTENT,
    NEGATIVE_CONTENT,
    NEUTRAL_CONTENT,
    ANXIETY_CONTENT,
    CALM_CONTENT
)


class TestCreateEntry:
    """Tests for POST /api/v1/entries"""

    def test_create_entry_success(self, client, auth_headers):
        """Test successful entry creation with emotion analysis."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data())
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        entry = data["data"]
        assert "id" in entry
        assert entry["raw_content"] == entry_data()["raw_content"]
        assert entry["status"] == "analyzed"
        assert "analysis" in entry
        assert "draft_title" in entry
        assert "draft_content" in entry

    def test_create_entry_positive_emotion(self, client, auth_headers):
        """Test entry creation with positive content."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=POSITIVE_CONTENT
        ))
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        assert analysis["primary_emotion"] in ["开心", "平静"]

    def test_create_entry_negative_emotion(self, client, auth_headers):
        """Test entry creation with negative content."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=NEGATIVE_CONTENT
        ))
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        assert analysis["primary_emotion"] in ["焦虑", "难过"]
        assert analysis["emotion_score"] < 60

    def test_create_entry_neutral_content(self, client, auth_headers):
        """Test entry creation with neutral content."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=NEUTRAL_CONTENT
        ))
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        # Neutral content should map to neutral or calm
        assert analysis["primary_emotion"] in ["中性", "平静"]

    def test_create_entry_anxiety_content(self, client, auth_headers):
        """Test entry creation with anxiety-related content."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=ANXIETY_CONTENT
        ))
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        assert analysis["primary_emotion"] == "焦虑"

    def test_create_entry_calm_content(self, client, auth_headers):
        """Test entry creation with calm-related content."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=CALM_CONTENT
        ))
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        assert analysis["primary_emotion"] == "平静"

    def test_create_entry_empty_content(self, client, auth_headers):
        """Test entry creation with empty content fails."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            raw_content=""
        ))
        assert response.status_code == 422

    def test_create_entry_no_auth(self, client):
        """Test entry creation without authentication fails."""
        response = client.post("/api/v1/entries", json=entry_data())
        assert response.status_code == 401

    def test_create_entry_invalid_input_type(self, client, auth_headers):
        """Test entry creation with non-text input type fails."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data(
            input_type="voice"  # Not supported yet
        ))
        assert response.status_code == 400

    def test_analysis_includes_all_fields(self, client, auth_headers):
        """Test that analysis response includes all required fields."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data())
        assert response.status_code == 201
        data = response.json()
        analysis = data["data"]["analysis"]
        required_fields = [
            "id", "primary_emotion", "secondary_emotions",
            "emotion_score", "valence", "arousal", "intensity",
            "risk_level", "summary", "suggestion"
        ]
        for field in required_fields:
            assert field in analysis

    def test_draft_fields_populated(self, client, auth_headers):
        """Test that draft fields are populated."""
        response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data())
        assert response.status_code == 201
        data = response.json()
        entry = data["data"]
        assert entry["draft_title"]
        assert entry["draft_content"]
