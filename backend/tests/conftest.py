"""
Pytest configuration and shared fixtures for InnerGarden API tests.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, get_db
from app.main import app


# In-memory SQLite database for testing
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db) -> Session:
    """Create a database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client):
    """Create a test user and return user data with token."""
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "role": "user"
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


@pytest.fixture(scope="function")
def admin_user(client):
    """Create an admin user and return user data with token."""
    user_data = {
        "username": "adminuser",
        "email": "adminuser@example.com",
        "password": "adminpass123",
        "role": "admin"
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


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Return authentication headers for a regular user."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture(scope="function")
def admin_headers(admin_user):
    """Return authentication headers for an admin user."""
    return {"Authorization": f"Bearer {admin_user['token']}"}


@pytest.fixture(scope="function")
def sample_entry(client, auth_headers):
    """Create a sample entry with emotion analysis."""
    entry_data = {
        "raw_content": "今天天气真好，心情很愉快！",
        "input_type": "text",
        "source_language": "zh-CN"
    }
    response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture(scope="function")
def sample_diary(client, auth_headers, sample_entry):
    """Create a sample diary from an entry."""
    from datetime import date
    diary_data = {
        "entry_id": sample_entry["id"],
        "title": "测试日记",
        "content": "这是一篇测试日记的内容",
        "diary_date": date.today().isoformat(),
        "is_favorite": False
    }
    response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data)
    assert response.status_code == 201
    return response.json()["data"]
