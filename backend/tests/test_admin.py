"""
Tests for admin endpoints.
"""

import pytest


class TestAdminUsers:
    """Tests for GET /api/v1/admin/users"""

    def test_admin_list_users_success(self, client, admin_headers):
        """Test admin can list all users."""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        users = data["data"]
        assert isinstance(users, list)
        # Admin user should be in the list
        assert any(u["email"] == "adminuser@example.com" for u in users)

    def test_admin_list_users_includes_all(self, client, admin_headers, test_user):
        """Test admin list includes regular users."""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()["data"]
        # Should find both admin and regular user
        emails = [u["email"] for u in users]
        assert "adminuser@example.com" in emails
        assert "testuser@example.com" in emails

    def test_admin_list_users_regular_forbidden(self, client, auth_headers):
        """Test regular user cannot list all users."""
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_list_users_no_auth(self, client):
        """Test listing users without authentication fails."""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401


class TestAdminStats:
    """Tests for GET /api/v1/admin/stats"""

    def test_admin_stats_success(self, client, admin_headers):
        """Test admin can get global stats."""
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        stats = data["data"]
        assert "total_users" in stats
        assert "total_entries" in stats
        assert "total_diaries" in stats
        assert "new_diaries_last_7_days" in stats
        # All values should be non-negative integers
        for key, value in stats.items():
            assert isinstance(value, int)
            assert value >= 0

    def test_admin_stats_includes_data(self, client, admin_headers, test_user, sample_diary):
        """Test admin stats reflect actual data."""
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        stats = response.json()["data"]
        # Should have at least the users we created
        assert stats["total_users"] >= 2  # admin + test_user
        # Should have entries and diaries
        assert stats["total_entries"] >= 1
        assert stats["total_diaries"] >= 1

    def test_admin_stats_regular_forbidden(self, client, auth_headers):
        """Test regular user cannot get global stats."""
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_stats_no_auth(self, client):
        """Test getting stats without authentication fails."""
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401
