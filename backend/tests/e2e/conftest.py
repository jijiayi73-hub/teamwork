"""
Shared fixtures for E2E flow tests.

These fixtures provide common setup for testing complete user journeys.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Mock openai module before importing app
sys.modules['openai'] = MagicMock()
sys.modules['openai.OpenAI'] = MagicMock
sys.modules['openai.api_key'] = MagicMock
sys.modules['openai.APITimeoutError'] = Exception
sys.modules['openai.RateLimitError'] = Exception
sys.modules['openai.APIError'] = Exception

from app.database import Base, get_db
from app.main import app
from app.models.diary import User, Diary, EmotionAnalysis, Entry
from app.models.chat import Conversation, Message
from tests.chat_test_utils import FakeAIProvider


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
def authenticated_user(client):
    """
    Create and authenticate a user, return user data with token.

    This is the primary fixture for E2E tests - it creates a fresh user
    for each test and returns the authentication credentials.
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    user_data = {
        "username": f"e2e_user_{unique_id}",
        "email": f"e2e_{unique_id}@example.com",
        "password": "e2e_test_pass123",
        "role": "user"
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"

    data = response.json()
    return {
        "id": data["data"]["user"]["id"],
        "username": data["data"]["user"]["username"],
        "email": data["data"]["user"]["email"],
        "token": data["data"]["access_token"],
        "user": data["data"]["user"]
    }


@pytest.fixture(scope="function")
def auth_headers(authenticated_user):
    """Return authentication headers for E2E tests."""
    return {"Authorization": f"Bearer {authenticated_user['token']}"}


@pytest.fixture(scope="function")
def authenticated_admin(client):
    """Create and authenticate an admin user."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    admin_data = {
        "username": f"e2e_admin_{unique_id}",
        "email": f"e2e_admin_{unique_id}@example.com",
        "password": "admin_test_pass123",
        "role": "admin"
    }

    response = client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201

    data = response.json()
    return {
        "id": data["data"]["user"]["id"],
        "username": data["data"]["user"]["username"],
        "email": data["data"]["user"]["email"],
        "token": data["data"]["access_token"]
    }


@pytest.fixture(scope="function")
def admin_headers(authenticated_admin):
    """Return authentication headers for admin user."""
    return {"Authorization": f"Bearer {authenticated_admin['token']}"}


@pytest.fixture(scope="function")
def sample_entry(client, auth_headers):
    """Create a sample entry with emotion analysis for E2E tests."""
    entry_data = {
        "raw_content": "今天天气真好，心情很愉快！和朋友一起去了公园，看到了美丽的花朵。",
        "input_type": "text",
        "source_language": "zh-CN"
    }
    response = client.post("/api/v1/entries", headers=auth_headers, json=entry_data)
    assert response.status_code == 201, f"Entry creation failed: {response.text}"
    return response.json()["data"]


@pytest.fixture(scope="function")
def sample_diary(client, auth_headers, sample_entry):
    """Create a sample diary from an entry for E2E tests."""
    diary_data = {
        "entry_id": sample_entry["id"],
        "title": sample_entry.get("draft_title", "测试日记"),
        "content": sample_entry.get("draft_content", "这是测试日记内容"),
        "diary_date": date.today().isoformat(),
        "is_favorite": False
    }
    response = client.post("/api/v1/diaries", headers=auth_headers, json=diary_data)
    assert response.status_code == 201, f"Diary creation failed: {response.text}"
    return response.json()["data"]


@pytest.fixture(scope="function")
def fake_ai_provider():
    """Provide a fake AI provider for chat E2E tests."""
    provider = FakeAIProvider()
    provider.set_response("这是测试回复，我在听你说话。")
    return provider


@pytest.fixture(scope="function")
def client_with_fake_ai(client, fake_ai_provider):
    """Create a test client with mocked AI provider."""
    with patch("app.services.ai_provider.get_provider", return_value=fake_ai_provider):
        yield client


@pytest.fixture(scope="function")
def second_user(client):
    """Create a second user for isolation tests."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    user_data = {
        "username": f"e2e_second_{unique_id}",
        "email": f"second_{unique_id}@example.com",
        "password": "second_test_pass123",
        "role": "user"
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    data = response.json()
    return {
        "id": data["data"]["user"]["id"],
        "username": data["data"]["user"]["username"],
        "email": data["data"]["user"]["email"],
        "token": data["data"]["access_token"],
        "headers": {"Authorization": f"Bearer {data['data']['access_token']}"}
    }


class E2EHelper:
    """Helper class for common E2E operations."""

    def __init__(self, client, auth_headers):
        self.client = client
        self.auth_headers = auth_headers

    def create_complete_diary(self, content: str = "今天感觉很平静，写完日记后心情更好了。"):
        """Create an entry and diary in one call."""
        entry_response = self.client.post(
            "/api/v1/entries",
            headers=self.auth_headers,
            json={"raw_content": content, "input_type": "text", "source_language": "zh-CN"}
        )
        assert entry_response.status_code == 201
        entry = entry_response.json()["data"]

        diary_response = self.client.post(
            "/api/v1/diaries",
            headers=self.auth_headers,
            json={
                "entry_id": entry["id"],
                "title": entry.get("draft_title", "日记标题"),
                "content": entry.get("draft_content", content),
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        assert diary_response.status_code == 201
        return entry, diary_response.json()["data"]

    def create_chat_conversation(self, message: str = "你好，我想聊聊今天的事情"):
        """Create a new chat conversation."""
        response = self.client.post(
            "/api/v1/chat/messages",
            headers=self.auth_headers,
            json={"mode": "companion", "content": message, "use_memory": False}
        )
        assert response.status_code == 200
        return response.json()["data"]

    def upload_test_image(self):
        """Upload a test image for memory cards."""
        import base64
        # Create a minimal valid PNG (1x1 pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        data_url = f"data:image/png;base64,{base64.b64encode(png_data).decode()}"

        response = self.client.post(
            "/api/v1/uploads/images",
            headers=self.auth_headers,
            json={
                "filename": "test_cover.png",
                "content_type": "image/png",
                "data_url": data_url
            }
        )
        assert response.status_code in [200, 201]  # Accept both 200 and 201
        return response.json()["data"]["url"]


@pytest.fixture(scope="function")
def e2e_helper(client, auth_headers):
    """Provide an E2E helper instance."""
    return E2EHelper(client, auth_headers)
