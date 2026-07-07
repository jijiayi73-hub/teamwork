"""
Tests for authentication endpoints.
"""

import pytest

from tests.factories import user_data, login_data
from tests.helpers import assert_error_response, assert_validation_error


class TestUserRegistration:
    """Tests for POST /api/v1/auth/register"""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username="newuser",
            email="newuser@example.com"
        ))
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["user"]["username"] == "newuser"
        assert data["data"]["user"]["email"] == "newuser@example.com"
        assert data["data"]["user"]["role"] == "user"

    def test_register_admin_success(self, client):
        """Test successful admin registration."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username="admin",
            email="admin@example.com",
            role="admin"
        ))
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["user"]["role"] == "admin"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username="different",
            email=test_user["email"]  # Same email as test_user
        ))
        assert response.status_code == 409

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username fails."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username=test_user["username"],  # Same username
            email="different@example.com"
        ))
        assert response.status_code == 409

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/api/v1/auth/register", json=user_data(
            email="notanemail"
        ))
        assert response.status_code == 422

    def test_register_short_username(self, client):
        """Test registration with username below minimum length."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username="a"  # Too short (min 2)
        ))
        assert response.status_code == 422

    def test_register_long_username(self, client):
        """Test registration with username above maximum length."""
        response = client.post("/api/v1/auth/register", json=user_data(
            username="a" * 51  # Too long (max 50)
        ))
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with password below minimum length."""
        response = client.post("/api/v1/auth/register", json=user_data(
            password="12345"  # Too short (min 6)
        ))
        assert response.status_code == 422


class TestUserLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, test_user):
        """Test successful user login."""
        response = client.post("/api/v1/auth/login", json=login_data(
            email=test_user["email"],
            password="testpass123"
        ))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "user" in data["data"]

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post("/api/v1/auth/login", json=login_data(
            email=test_user["email"],
            password="wrongpassword"
        ))
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post("/api/v1/auth/login", json=login_data(
            email="nonexistent@example.com",
            password="anypassword"
        ))
        assert response.status_code == 401

    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format."""
        response = client.post("/api/v1/auth/login", json={
            "email": "notanemail",
            "password": "anypassword"
        })
        assert response.status_code == 422


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me"""

    def test_get_current_user_success(self, client, auth_headers):
        """Test getting current user with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "id" in data["data"]
        assert "username" in data["data"]
        assert "email" in data["data"]

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalidtoken123"
        })
        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, client):
        """Test getting current user with malformed authorization header."""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "InvalidFormat token"
        })
        assert response.status_code == 401
