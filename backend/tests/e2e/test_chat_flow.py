"""
F-003: Chat Full Flow Tests

Tests the complete chat lifecycle:
1. Create New Conversation → Send Message → Receive AI Reply → Continue → View History → Delete
"""
from datetime import date
from unittest.mock import patch
import pytest


class TestChatFullFlow:
    """Test the complete chat flow with conversation and message management."""

    def test_complete_chat_flow(self, client_with_fake_ai, auth_headers, db_session):
        """
        Test: Create Conversation → Send Message → Continue → List → Get Messages → Delete

        This is the F-003 main flow test.
        """
        # Step 1: Create new conversation by sending first message
        message_response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={
                "mode": "companion",
                "content": "你好，今天感觉很累，想聊聊工作压力。",
                "use_memory": False
            }
        )
        assert message_response.status_code == 200
        chat_data = message_response.json()["data"]

        # Verify response structure
        assert "conversation" in chat_data
        assert "user_message" in chat_data
        assert "assistant_message" in chat_data
        assert chat_data["user_message"]["role"] == "user"
        assert chat_data["assistant_message"]["role"] == "assistant"

        conversation_id = chat_data["conversation"]["id"]
        assert conversation_id > 0
        assert chat_data["conversation"]["mode"] == "companion"
        assert chat_data["conversation"]["message_count"] == 2

        # Verify database state
        from app.models.chat import Conversation, Message
        conv = db_session.get(Conversation, conversation_id)
        assert conv is not None
        assert conv.mode == "companion"

        messages = db_session.query(Message).filter_by(conversation_id=conversation_id).all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

        # Step 2: Continue the conversation
        continue_response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={
                "conversation_id": conversation_id,
                "content": "主要是有太多deadline要赶，感觉时间不够用。",
                "use_memory": False
            }
        )
        assert continue_response.status_code == 200
        continue_data = continue_response.json()["data"]

        # Verify same conversation
        assert continue_data["conversation"]["id"] == conversation_id
        assert continue_data["conversation"]["message_count"] == 4  # 2 new messages

        # Step 3: List conversations
        list_response = client_with_fake_ai.get(
            "/api/v1/chat/conversations",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        list_data = list_response.json()["data"]
        assert list_data["total"] == 1
        assert len(list_data["conversations"]) == 1
        assert list_data["conversations"][0]["id"] == conversation_id

        # Step 4: Get conversation detail
        detail_response = client_with_fake_ai.get(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200
        detail_data = detail_response.json()["data"]
        assert detail_data["conversation"]["id"] == conversation_id
        assert detail_data["conversation"]["message_count"] == 4

        # Step 5: Get message history
        messages_response = client_with_fake_ai.get(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=auth_headers
        )
        assert messages_response.status_code == 200
        messages_data = messages_response.json()["data"]

        assert messages_data["total"] == 4
        assert len(messages_data["messages"]) == 4

        # Verify message order (oldest to newest)
        messages = messages_data["messages"]
        assert messages[0]["message"]["role"] == "user"
        assert messages[1]["message"]["role"] == "assistant"
        assert messages[2]["message"]["role"] == "user"
        assert messages[3]["message"]["role"] == "assistant"

        # Verify content
        assert "工作压力" in messages[0]["message"]["content"]
        assert "deadline" in messages[2]["message"]["content"]

        # Step 6: Delete conversation
        delete_response = client_with_fake_ai.delete(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify deleted from list
        list_after = client_with_fake_ai.get(
            "/api/v1/chat/conversations",
            headers=auth_headers
        )
        assert list_after.json()["data"]["total"] == 0

        # Verify soft delete in database
        conv = db_session.get(Conversation, conversation_id)
        assert conv.deleted_at is not None

    def test_create_conversation_explicitly(self, client_with_fake_ai, auth_headers):
        """Test explicitly creating a conversation before sending messages."""
        # Create companion conversation
        create_response = client_with_fake_ai.post(
            "/api/v1/chat/conversations",
            headers=auth_headers,
            json={"mode": "companion", "title": "测试对话"}
        )
        assert create_response.status_code == 201
        conv = create_response.json()["data"]["conversation"]
        assert conv["mode"] == "companion"
        assert conv["title"] == "测试对话"

        # Send message in the created conversation
        message_response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={
                "conversation_id": conv["id"],
                "content": "测试消息"
            }
        )
        assert message_response.status_code == 200

    def test_multiple_conversations(self, client_with_fake_ai, auth_headers):
        """Test managing multiple conversations."""
        # Create first conversation
        response1 = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "第一篇对话"}
        )
        conv1_id = response1.json()["data"]["conversation"]["id"]

        # Create second conversation
        response2 = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "第二篇对话"}
        )
        conv2_id = response2.json()["data"]["conversation"]["id"]

        # List conversations
        list_response = client_with_fake_ai.get(
            "/api/v1/chat/conversations",
            headers=auth_headers
        )
        conversations = list_response.json()["data"]["conversations"]
        assert len(conversations) == 2

        # Verify pagination
        page1_response = client_with_fake_ai.get(
            "/api/v1/chat/conversations?page=1&page_size=1",
            headers=auth_headers
        )
        page1_data = page1_response.json()["data"]
        assert len(page1_data["conversations"]) == 1
        assert page1_data["total"] == 2

    def test_past_self_chat_flow(self, client_with_fake_ai, auth_headers, db_session, sample_diary):
        """Test Past Self chat flow with anchor diary."""
        # Create past_self conversation with anchor diary
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={
                "mode": "past_self",
                "anchor_diary_id": sample_diary["id"],
                "content": "那天的我想提醒我什么？",
                "use_memory": False
            }
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # Verify past_self mode
        assert data["conversation"]["mode"] == "past_self"
        assert data["conversation"]["anchor_diary_id"] == sample_diary["id"]

        # Verify database
        from app.models.chat import Conversation
        conv_id = data["conversation"]["id"]
        conv = db_session.get(Conversation, conv_id)
        assert conv.mode == "past_self"
        assert conv.anchor_diary_id == sample_diary["id"]


class TestChatPaginationAndFiltering:
    """Test chat conversation pagination and filtering."""

    def test_conversation_pagination(self, client_with_fake_ai, auth_headers):
        """Test conversation list pagination."""
        # Create 5 conversations
        for i in range(5):
            client_with_fake_ai.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"mode": "companion", "content": f"对话 {i}"}
            )

        # First page
        page1 = client_with_fake_ai.get(
            "/api/v1/chat/conversations?page=1&page_size=2",
            headers=auth_headers
        )
        page1_data = page1.json()["data"]
        assert len(page1_data["conversations"]) == 2
        assert page1_data["total"] == 5
        assert page1_data["page"] == 1

        # Second page
        page2 = client_with_fake_ai.get(
            "/api/v1/chat/conversations?page=2&page_size=2",
            headers=auth_headers
        )
        page2_data = page2.json()["data"]
        assert len(page2_data["conversations"]) == 2

        # Third page (1 item)
        page3 = client_with_fake_ai.get(
            "/api/v1/chat/conversations?page=3&page_size=2",
            headers=auth_headers
        )
        page3_data = page3.json()["data"]
        assert len(page3_data["conversations"]) == 1

    def test_conversation_mode_filter(self, client_with_fake_ai, auth_headers, sample_diary):
        """Test filtering conversations by mode."""
        # Create companion conversations
        client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "Companion chat"}
        )

        # Create past_self conversation
        client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "past_self", "anchor_diary_id": sample_diary["id"], "content": "Past self"}
        )

        # Filter by companion mode
        companion_response = client_with_fake_ai.get(
            "/api/v1/chat/conversations?mode=companion",
            headers=auth_headers
        )
        companion_data = companion_response.json()["data"]
        assert len(companion_data["conversations"]) == 1
        assert companion_data["conversations"][0]["mode"] == "companion"

        # Filter by past_self mode
        past_response = client_with_fake_ai.get(
            "/api/v1/chat/conversations?mode=past_self",
            headers=auth_headers
        )
        past_data = past_response.json()["data"]
        assert len(past_data["conversations"]) == 1
        assert past_data["conversations"][0]["mode"] == "past_self"

    def test_message_pagination(self, client_with_fake_ai, auth_headers):
        """Test message pagination within a conversation."""
        # Create conversation with multiple messages
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "开始"}
        )
        conv_id = response.json()["data"]["conversation"]["id"]

        # Add more messages
        for i in range(4):
            client_with_fake_ai.post(
                "/api/v1/chat/messages",
                headers=auth_headers,
                json={"conversation_id": conv_id, "content": f"消息 {i}"}
            )

        # Get first page
        page1 = client_with_fake_ai.get(
            f"/api/v1/chat/conversations/{conv_id}/messages?page=1&page_size=3",
            headers=auth_headers
        )
        page1_data = page1.json()["data"]
        assert len(page1_data["messages"]) == 3
        assert page1_data["total"] == 10  # 5 rounds * 2 messages


class TestChatErrorsAndEdgeCases:
    """Test error handling and edge cases in chat flow."""

    def test_send_message_to_nonexistent_conversation(self, client_with_fake_ai, auth_headers):
        """Test sending message to non-existent conversation."""
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"conversation_id": 99999, "content": "测试"}
        )
        assert response.status_code == 404

    def test_create_past_self_without_anchor(self, client_with_fake_ai, auth_headers):
        """Test creating past_self conversation without anchor_diary_id."""
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "past_self", "content": "测试"}
        )
        assert response.status_code == 422  # Validation error

    def test_chat_requires_authentication(self, client_with_fake_ai):
        """Test that chat endpoints require authentication."""
        # Send message without auth
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            json={"mode": "companion", "content": "测试"}
        )
        assert response.status_code == 401

        # List conversations without auth
        response = client_with_fake_ai.get("/api/v1/chat/conversations")
        assert response.status_code == 401

    def test_empty_content_validation(self, client_with_fake_ai, auth_headers):
        """Test that empty content is rejected."""
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": ""}
        )
        assert response.status_code == 422


class TestChatDatabaseIntegrity:
    """Test database integrity for chat operations."""

    def test_conversation_soft_delete(self, client_with_fake_ai, auth_headers, db_session):
        """Test that conversation deletion is soft delete."""
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": "测试"}
        )
        conv_id = response.json()["data"]["conversation"]["id"]

        # Delete
        client_with_fake_ai.delete(
            f"/api/v1/chat/conversations/{conv_id}",
            headers=auth_headers
        )

        # Verify still in database
        from app.models.chat import Conversation
        conv = db_session.get(Conversation, conv_id)
        assert conv is not None
        assert conv.deleted_at is not None

    def test_messages_persisted_correctly(self, client_with_fake_ai, auth_headers, db_session):
        """Test that messages are correctly persisted with proper roles and content."""
        user_content = "用户消息内容"
        response = client_with_fake_ai.post(
            "/api/v1/chat/messages",
            headers=auth_headers,
            json={"mode": "companion", "content": user_content}
        )
        conv_id = response.json()["data"]["conversation"]["id"]

        from app.models.chat import Message
        messages = db_session.query(Message).filter_by(
            conversation_id=conv_id
        ).order_by(Message.created_at).all()

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == user_content
        assert messages[1].role == "assistant"
        assert messages[1].content is not None
