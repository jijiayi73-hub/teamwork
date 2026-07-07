"""
Tests for logs endpoints.
"""

import pytest
from datetime import datetime, timezone


class TestClientLogs:
    """Tests for POST /api/v1/logs/client"""

    def test_send_client_logs_success(self, client, auth_headers):
        """Test successfully sending client logs."""
        log_payload = {
            "logs": [
                {
                    "level": "info",
                    "args": ["Test message"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "url": "http://localhost:5173/test"
                },
                {
                    "level": "error",
                    "args": ["Error occurred"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "url": "http://localhost:5173/test",
                    "message": "Something went wrong"
                }
            ]
        }
        response = client.post("/api/v1/logs/client", headers=auth_headers, json=log_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["received"] == 2
        assert "user_id" in data["data"]

    def test_send_client_logs_empty(self, client, auth_headers):
        """Test sending empty log array."""
        response = client.post("/api/v1/logs/client", headers=auth_headers, json={"logs": []})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["received"] == 0

    def test_send_client_logs_single(self, client, auth_headers):
        """Test sending a single log entry."""
        log_payload = {
            "logs": [
                {
                    "level": "warn",
                    "args": ["Warning message"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        response = client.post("/api/v1/logs/client", headers=auth_headers, json=log_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["received"] == 1

    def test_send_client_logs_multiple_levels(self, client, auth_headers):
        """Test sending logs with various levels."""
        log_payload = {
            "logs": [
                {"level": "info", "args": [], "timestamp": datetime.now(timezone.utc).isoformat()},
                {"level": "warn", "args": [], "timestamp": datetime.now(timezone.utc).isoformat()},
                {"level": "error", "args": [], "timestamp": datetime.now(timezone.utc).isoformat()}
            ]
        }
        response = client.post("/api/v1/logs/client", headers=auth_headers, json=log_payload)
        assert response.status_code == 200

    def test_send_client_logs_no_auth(self, client):
        """Test sending logs without authentication fails."""
        response = client.post("/api/v1/logs/client", json={"logs": []})
        assert response.status_code == 401

    def test_send_client_logs_invalid_payload(self, client, auth_headers):
        """Test sending invalid payload."""
        # Missing logs field
        response = client.post("/api/v1/logs/client", headers=auth_headers, json={})
        assert response.status_code == 422


class TestLogsStats:
    """Tests for GET /api/v1/logs/stats"""

    def test_get_logs_stats_success(self, client, auth_headers):
        """Test getting logs stats."""
        response = client.get("/api/v1/logs/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert "message" in data["data"]

    def test_get_logs_stats_no_auth(self, client):
        """Test getting logs stats without authentication fails."""
        response = client.get("/api/v1/logs/stats")
        assert response.status_code == 401
