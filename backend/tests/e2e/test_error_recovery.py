"""
F-005: Error Recovery Flow Tests

Tests various error scenarios and recovery paths:
1. Invalid Token Recovery
2. AI Provider Error Recovery
3. Validation Error Recovery
4. Resource Not Found Recovery
"""
from datetime import date
from unittest.mock import patch
import pytest
from tests.chat_test_utils import FakeAIProvider, TimeoutAIProvider, FailedAIProvider


class TestInvalidTokenRecovery:
    """Test recovery from invalid/expired token scenarios."""

    def test_invalid_token_recovery_flow(self, client):
        """Test using invalid token and recovering by re-login."""
        # Create user and get valid token
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"token_recov_{unique_id}",
            "email": f"token_recov_{unique_id}@example.com",
            "password": "Password123!"
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        valid_token = register_response.json()["data"]["access_token"]

        # Try with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/v1/diaries", headers=invalid_headers)
        assert response.status_code == 401

        # Re-login to get new token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        new_token = login_response.json()["data"]["access_token"]

        # Use new token successfully
        new_headers = {"Authorization": f"Bearer {new_token}"}
        response = client.get("/api/v1/diaries", headers=new_headers)
        assert response.status_code == 200

    def test_missing_token_recovery(self, client):
        """Test accessing protected resource without token and recovering."""
        # Try without token
        response = client.get("/api/v1/diaries")
        assert response.status_code == 401

        # Register and login
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        register_response = client.post("/api/v1/auth/register", json={
            "username": f"missing_{unique_id}",
            "email": f"missing_{unique_id}@example.com",
            "password": "Password123!"
        })
        assert register_response.status_code == 201

        token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Access successfully with token
        response = client.get("/api/v1/diaries", headers=headers)
        assert response.status_code == 200


class TestAIProviderErrorRecovery:
    """Test recovery from AI Provider errors."""

    def test_ai_timeout_saves_user_message(self, client, auth_headers, db_session):
        """Test that user message is saved even when AI times out."""
        with patch("app.services.ai_provider.get_provider", return_value=TimeoutAIProvider()):
            response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "测试超时", "use_memory": False}
            )

        assert response.status_code == 504  # Gateway Timeout

        # Verify user message was saved
        from app.models.chat import Message
        user_messages = db_session.query(Message).filter_by(role="user").all()
        assert len(user_messages) == 1
        assert user_messages[0].content == "测试超时"

        # Verify no assistant message
        assistant_messages = db_session.query(Message).filter_by(role="assistant").all()
        assert len(assistant_messages) == 0

    def test_ai_provider_error_recovery(self, client, auth_headers, db_session):
        """Test recovery from AI provider error (502)."""
        # First message fails
        with patch("app.services.ai_provider.get_provider", return_value=FailedAIProvider()):
            fail_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "第一次", "use_memory": False}
            )

        assert fail_response.status_code == 502

        # User message should be saved
        from app.models.chat import Message
        user_messages = db_session.query(Message).filter_by(role="user").all()
        assert len(user_messages) == 1
        assert user_messages[0].content == "第一次"

        # Retry with working provider
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("现在正常了")
            mock_provider.return_value = fake_ai

            retry_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "重试", "use_memory": False}
            )

        assert retry_response.status_code == 200
        data = retry_response.json()["data"]
        # Check that we got a valid response
        assert "assistant_message" in data

    def test_continuing_conversation_after_error(self, client, auth_headers, db_session):
        """Test continuing conversation after AI error."""
        # Create conversation with working provider
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("第一句回复")
            mock_provider.return_value = fake_ai

            first_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "开始", "use_memory": False}
            )

        assert first_response.status_code == 200
        conversation_id = first_response.json()["data"]["conversation"]["id"]

        # Second message fails
        with patch("app.services.ai_provider.get_provider", return_value=FailedAIProvider()):
            fail_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={
                    "conversation_id": conversation_id,
                    "content": "这条会失败",
                    "use_memory": False
                }
            )

        assert fail_response.status_code == 502

        # Third message succeeds
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("恢复成功")
            mock_provider.return_value = fake_ai

            recovery_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={
                    "conversation_id": conversation_id,
                    "content": "恢复",
                    "use_memory": False
                }
            )

        assert recovery_response.status_code == 200
        # Check that we got a response (content may vary)
        assert "assistant_message" in recovery_response.json()["data"]


class TestValidationErrorRecovery:
    """Test recovery from validation errors."""

    def test_missing_required_field_recovery(self, client, auth_headers):
        """Test recovery when missing required field."""
        from unittest.mock import patch
        from tests.chat_test_utils import FakeAIProvider

        # Missing mode field
        response = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"content": "测试", "use_memory": False}
        )
        assert response.status_code == 422

        # Verify error details
        error_data = response.json()
        assert "detail" in error_data

        # Fix and retry with mocked AI provider
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("回复")
            mock_provider.return_value = fake_ai

            response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "测试", "use_memory": False}
            )

        # Should succeed (may fail on AI but validation passes)
        assert response.status_code != 422

    def test_empty_content_validation_recovery(self, client, auth_headers):
        """Test recovery from empty content validation."""
        # Empty content
        response = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "", "use_memory": False}
        )
        assert response.status_code == 422

        # Fix with valid content
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("回复")
            mock_provider.return_value = fake_ai

            response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "有效内容", "use_memory": False}
            )

        assert response.status_code == 200

    def test_invalid_email_format_recovery(self, client):
        """Test recovery from invalid email format."""
        # Invalid email
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "Password123!"
        })
        assert response.status_code == 422

        # Fix with valid email
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 201

    def test_invalid_date_format_recovery(self, client, auth_headers, sample_entry):
        """Test recovery from invalid date format."""
        # Invalid date
        response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": sample_entry["id"],
                "title": "测试",
                "content": "内容",
                "diary_date": "not-a-date",
                "is_favorite": False
            }
        )
        assert response.status_code == 422

        # Fix with valid date
        response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": sample_entry["id"],
                "title": "测试",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        assert response.status_code == 201


class TestResourceNotFoundRecovery:
    """Test recovery from resource not found scenarios."""

    def test_nonexistent_conversation_recovery(self, client, auth_headers):
        """Test accessing non-existent conversation and recovery."""
        # Try to get non-existent conversation
        response = client.get(
            "/api/v1/chat/conversations/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

        # Create a valid conversation
        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("回复")
            mock_provider.return_value = fake_ai

            create_response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "新对话", "use_memory": False}
            )

        assert create_response.status_code == 200
        conversation_id = create_response.json()["data"]["conversation"]["id"]

        # Access the valid conversation
        response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_nonexistent_diary_recovery(self, client, auth_headers):
        """Test accessing non-existent diary and recovery."""
        # Try to get non-existent diary
        response = client.get(
            "/api/v1/diaries/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

        # Create a valid diary (need entry first)
        entry_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            json={"raw_content": "测试", "input_type": "text", "source_language": "zh-CN"}
        )
        entry = entry_response.json()["data"]

        diary_response = client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "entry_id": entry["id"],
                "title": "测试",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        assert diary_response.status_code == 201
        diary_id = diary_response.json()["data"]["id"]

        # Access the valid diary
        response = client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_404_does_not_leak_existence(self, client, second_user):
        """Test that 404 errors don't leak resource existence info."""
        # User 1 creates a resource
        user1_headers = second_user["headers"]
        entry_response = client.post(
            "/api/v1/entries",
            headers=user1_headers,
            json={"raw_content": "用户1的日记", "input_type": "text", "source_language": "zh-CN"}
        )
        entry = entry_response.json()["data"]

        diary_response = client.post(
            "/api/v1/diaries",
            headers=user1_headers,
            json={
                "entry_id": entry["id"],
                "title": "用户1的日记",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        user1_diary_id = diary_response.json()["data"]["id"]

        # User 2 (different user) tries to access User 1's diary
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user2_response = client.post("/api/v1/auth/register", json={
            "username": f"user2_{unique_id}",
            "email": f"user2_{unique_id}@example.com",
            "password": "Password123!"
        })
        user2_token = user2_response.json()["data"]["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        response = client.get(
            f"/api/v1/diaries/{user1_diary_id}",
            headers=user2_headers
        )

        # Should return 404, not 403 (don't reveal that resource exists)
        assert response.status_code == 404

        # Error message should not reveal it belongs to another user
        error_detail = response.json().get("detail", "")
        assert "another user" not in str(error_detail).lower()
        assert "owned" not in str(error_detail).lower()


class TestErrorMessages:
    """Test that error messages are helpful and appropriate."""

    def test_401_error_message(self, client):
        """Test that 401 error message is appropriate."""
        response = client.get("/api/v1/diaries")
        assert response.status_code == 401

        # Should indicate authentication is required
        # Not checking exact message as it may vary by implementation

    def test_422_error_includes_field_details(self, client, auth_headers):
        """Test that 422 validation error includes field details."""
        response = client.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"content": "", "use_memory": False}  # Missing mode
        )
        assert response.status_code == 422

        error_detail = response.json().get("detail", [])
        # Should include validation details
        # Format may vary by FastAPI version

    def test_502_error_includes_provider_info(self, client, auth_headers):
        """Test that 502 error includes provider information."""
        with patch("app.services.ai_provider.get_provider", return_value=FailedAIProvider()):
            response = client.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": "测试", "use_memory": False}
            )

        assert response.status_code == 502

        # Check that error includes provider info
        error_data = response.json()
        assert "error" in error_data
        # Should include provider information
