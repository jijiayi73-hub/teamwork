"""
Helper functions for testing InnerGarden API.
"""

from typing import Any, Optional


def create_user(client, username: str, email: str, password: str = "testpass123", role: str = "user") -> dict:
    """Create a user and return user data with token."""
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    return {
        "id": data["data"]["user"]["id"],
        "username": data["data"]["user"]["username"],
        "email": data["data"]["user"]["email"],
        "token": data["data"]["access_token"]
    }


def login_user(client, email: str, password: str) -> dict:
    """Login a user and return token."""
    login_data = {"email": email, "password": password}
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    return {"token": data["data"]["access_token"]}


def create_entry(client, token: str, content: str = "今天心情不错") -> dict:
    """Create an entry and return entry data."""
    entry_data = {
        "raw_content": content,
        "input_type": "text",
        "source_language": "zh-CN"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/entries", headers=headers, json=entry_data)
    assert response.status_code == 201
    return response.json()["data"]


def create_diary(client, token: str, entry_id: int, title: str = "测试日记", content: str = "测试内容") -> dict:
    """Create a diary and return diary data."""
    from datetime import date
    diary_data = {
        "entry_id": entry_id,
        "title": title,
        "content": content,
        "diary_date": date.today().isoformat(),
        "is_favorite": False
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/diaries", headers=headers, json=diary_data)
    assert response.status_code == 201
    return response.json()["data"]


def assert_error_response(response, expected_status: int, expected_detail_contains: Optional[str] = None):
    """Assert that response is an error with expected status."""
    assert response.status_code == expected_status
    data = response.json()
    assert "success" in data or "detail" in data
    if expected_detail_contains:
        error_detail = data.get("detail", "")
        assert expected_detail_contains in error_detail


def assert_validation_error(response, field_name: str):
    """Assert that response is a validation error for a specific field."""
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Check that the error mentions the field
    detail_str = str(data["detail"])
    assert field_name in detail_str


def get_auth_headers(token: str) -> dict:
    """Return authorization headers with the given token."""
    return {"Authorization": f"Bearer {token}"}
