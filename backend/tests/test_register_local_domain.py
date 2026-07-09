"""
Quick test to verify registration with .local domain works.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_register_with_local_domain():
    """Test that registration accepts .local domain email."""
    client = TestClient(app)

    # Test with .local domain
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser_local",
            "email": "demo@innergarden.local",
            "password": "password123"
        }
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_register_normalizes_email():
    """Test that email is normalized to lowercase."""
    client = TestClient(app)

    # Test with uppercase .local domain
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser_upper",
            "email": "DEMO@InnerGarden.Local",
            "password": "password123"
        }
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "demo@innergarden.local"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
