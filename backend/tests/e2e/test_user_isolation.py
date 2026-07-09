"""
F-006: Multi-User Isolation Flow Tests

Tests that users' data is properly isolated:
1. User A and User B cannot access each other's resources
2. 404 errors don't leak information about other users' resources
3. List endpoints only return current user's resources
"""
from datetime import date
from unittest.mock import patch
import pytest
from tests.chat_test_utils import FakeAIProvider


class TestUserResourceIsolation:
    """Test that users cannot access each other's resources."""

    def test_users_cannot_access_each_others_diaries(self, client):
        """Test that users cannot access diaries owned by other users."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"user_a_{unique_id}",
            "email": f"user_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        assert user_a_response.status_code == 201
        user_a_token = user_a_response.json()["data"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

        # Create User A's diary
        entry_a = client.post(
            "/api/v1/entries",
            headers=user_a_headers,
            json={"raw_content": "用户A的日记内容", "input_type": "text", "source_language": "zh-CN"}
        )
        entry_a_data = entry_a.json()["data"]

        diary_a = client.post(
            "/api/v1/diaries",
            headers=user_a_headers,
            json={
                "entry_id": entry_a_data["id"],
                "title": "用户A的日记",
                "content": "这是用户A的日记",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        diary_a_id = diary_a.json()["data"]["id"]

        # Create User B
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"user_b_{unique_id}",
            "email": f"user_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        assert user_b_response.status_code == 201
        user_b_token = user_b_response.json()["data"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # User B tries to access User A's diary
        get_response = client.get(
            f"/api/v1/diaries/{diary_a_id}",
            headers=user_b_headers
        )
        assert get_response.status_code == 404

        # User B tries to update User A's diary
        update_response = client.patch(
            f"/api/v1/diaries/{diary_a_id}",
            headers=user_b_headers,
            json={"title": "试图修改"}
        )
        assert update_response.status_code == 404

        # User B tries to delete User A's diary
        delete_response = client.delete(
            f"/api/v1/diaries/{diary_a_id}",
            headers=user_b_headers
        )
        assert delete_response.status_code == 404

    def test_users_cannot_access_each_other_conversations(self, client):
        """Test that users cannot access chat conversations owned by other users."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A and their conversation
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"chat_a_{unique_id}",
            "email": f"chat_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_token = user_a_response.json()["data"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("用户A的AI回复")
            mock_provider.return_value = fake_ai

            chat_a = client.post(
                "/api/v1/chat/messages",
                headers=user_a_headers,
                json={"mode": "companion", "content": "用户A的消息", "use_memory": False}
            )

        conv_a_id = chat_a.json()["data"]["conversation"]["id"]

        # Create User B
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"chat_b_{unique_id}",
            "email": f"chat_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_token = user_b_response.json()["data"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # User B tries to access User A's conversation
        get_response = client.get(
            f"/api/v1/chat/conversations/{conv_a_id}",
            headers=user_b_headers
        )
        assert get_response.status_code == 404

        # User B tries to get User A's conversation messages
        messages_response = client.get(
            f"/api/v1/chat/conversations/{conv_a_id}/messages",
            headers=user_b_headers
        )
        assert messages_response.status_code == 404

        # User B tries to delete User A's conversation
        delete_response = client.delete(
            f"/api/v1/chat/conversations/{conv_a_id}",
            headers=user_b_headers
        )
        assert delete_response.status_code == 404

    def test_users_cannot_access_each_other_memories(self, client):
        """Test that users cannot access memory cards owned by other users."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A and their memory
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"mem_a_{unique_id}",
            "email": f"mem_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_token = user_a_response.json()["data"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

        # Create User A's diary and memory
        entry_a = client.post(
            "/api/v1/entries",
            headers=user_a_headers,
            json={"raw_content": "用户A的记忆", "input_type": "text", "source_language": "zh-CN"}
        )
        entry_a_data = entry_a.json()["data"]

        diary_a = client.post(
            "/api/v1/diaries",
            headers=user_a_headers,
            json={
                "entry_id": entry_a_data["id"],
                "title": "用户A的日记",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        diary_a_id = diary_a.json()["data"]["id"]

        memory_a = client.post(
            "/api/v1/memories",
            headers=user_a_headers,
            json={
                "diary_id": diary_a_id,
                "cover_image_url": "/uploads/test.png",
                "emotion_label": "neutral",
                "emotion_color": "#D3D3D3",
                "keywords": [],
                "conversation_summary": "用户A的记忆摘要"
            }
        )
        memory_a_id = memory_a.json()["data"]["id"]

        # Create User B
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"mem_b_{unique_id}",
            "email": f"mem_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_token = user_b_response.json()["data"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # User B tries to access User A's memory
        get_response = client.get(
            f"/api/v1/memories/{memory_a_id}",
            headers=user_b_headers
        )
        assert get_response.status_code == 404

        # User B tries to update User A's memory
        update_response = client.patch(
            f"/api/v1/memories/{memory_a_id}",
            headers=user_b_headers,
            json={"emotion_label": "joy"}
        )
        assert update_response.status_code == 404

        # User B tries to delete User A's memory
        delete_response = client.delete(
            f"/api/v1/memories/{memory_a_id}",
            headers=user_b_headers
        )
        assert delete_response.status_code == 404


class TestUserListIsolation:
    """Test that list endpoints only return current user's resources."""

    def test_diary_list_isolation(self, client):
        """Test that diary list only shows current user's diaries."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A with 2 diaries
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"list_a_{unique_id}",
            "email": f"list_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_headers = {"Authorization": f"Bearer {user_a_response.json()['data']['access_token']}"}

        for i in range(2):
            entry = client.post(
                "/api/v1/entries",
                headers=user_a_headers,
                json={"raw_content": f"用户A日记{i}", "input_type": "text", "source_language": "zh-CN"}
            )
            entry_data = entry.json()["data"]

            client.post(
                "/api/v1/diaries",
                headers=user_a_headers,
                json={
                    "entry_id": entry_data["id"],
                    "title": f"用户A日记{i}",
                    "content": "内容",
                    "diary_date": date.today().isoformat(),
                    "is_favorite": False
                }
            )

        # Create User B with 1 diary
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"list_b_{unique_id}",
            "email": f"list_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_headers = {"Authorization": f"Bearer {user_b_response.json()['data']['access_token']}"}

        entry_b = client.post(
            "/api/v1/entries",
            headers=user_b_headers,
            json={"raw_content": "用户B日记", "input_type": "text", "source_language": "zh-CN"}
        )
        entry_b_data = entry_b.json()["data"]

        client.post(
            "/api/v1/diaries",
            headers=user_b_headers,
            json={
                "entry_id": entry_b_data["id"],
                "title": "用户B日记",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )

        # User A sees only their 2 diaries
        list_a = client.get("/api/v1/diaries", headers=user_a_headers)
        assert len(list_a.json()["data"]) == 2

        # User B sees only their 1 diary
        list_b = client.get("/api/v1/diaries", headers=user_b_headers)
        assert len(list_b.json()["data"]) == 1

    def test_conversation_list_isolation(self, client):
        """Test that conversation list only shows current user's conversations."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"conv_a_{unique_id}",
            "email": f"conv_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_token = user_a_response.json()["data"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("回复")
            mock_provider.return_value = fake_ai

            # Create 2 conversations for User A
            for i in range(2):
                client.post(
                    "/api/v1/chat/messages",
                    headers=user_a_headers,
                    json={"mode": "companion", "content": f"用户A对话{i}", "use_memory": False}
                )

        # Create User B
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"conv_b_{unique_id}",
            "email": f"conv_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_token = user_b_response.json()["data"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        with patch("app.services.ai_provider.get_provider") as mock_provider:
            fake_ai = FakeAIProvider()
            fake_ai.set_response("回复")
            mock_provider.return_value = fake_ai

            # Create 1 conversation for User B
            client.post(
                "/api/v1/chat/messages",
                headers=user_b_headers,
                json={"mode": "companion", "content": "用户B对话", "use_memory": False}
            )

        # User A sees only their 2 conversations
        list_a = client.get("/api/v1/chat/conversations", headers=user_a_headers)
        assert list_a.json()["data"]["total"] == 2

        # User B sees only their 1 conversation
        list_b = client.get("/api/v1/chat/conversations", headers=user_b_headers)
        assert list_b.json()["data"]["total"] == 1

    def test_memory_list_isolation(self, client):
        """Test that memory list only shows current user's memories."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A with 2 memories
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"memlist_a_{unique_id}",
            "email": f"memlist_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_token = user_a_response.json()["data"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

        for i in range(2):
            entry = client.post(
                "/api/v1/entries",
                headers=user_a_headers,
                json={"raw_content": f"用户A记忆{i}", "input_type": "text", "source_language": "zh-CN"}
            )
            entry_data = entry.json()["data"]

            diary = client.post(
                "/api/v1/diaries",
                headers=user_a_headers,
                json={
                    "entry_id": entry_data["id"],
                    "title": f"用户A日记{i}",
                    "content": "内容",
                    "diary_date": date.today().isoformat(),
                    "is_favorite": False
                }
            )
            diary_id = diary.json()["data"]["id"]

            client.post(
                "/api/v1/memories",
                headers=user_a_headers,
                json={
                    "diary_id": diary_id,
                    "cover_image_url": "/uploads/test.png",
                    "emotion_label": "neutral",
                    "emotion_color": "#D3D3D3",
                    "keywords": [],
                    "conversation_summary": f"用户A记忆{i}"
                }
            )

        # Create User B with 1 memory
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"memlist_b_{unique_id}",
            "email": f"memlist_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_token = user_b_response.json()["data"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        entry_b = client.post(
            "/api/v1/entries",
            headers=user_b_headers,
            json={"raw_content": "用户B记忆", "input_type": "text", "source_language": "zh-CN"}
        )
        entry_b_data = entry_b.json()["data"]

        diary_b = client.post(
            "/api/v1/diaries",
            headers=user_b_headers,
            json={
                "entry_id": entry_b_data["id"],
                "title": "用户B日记",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )
        diary_b_id = diary_b.json()["data"]["id"]

        client.post(
            "/api/v1/memories",
            headers=user_b_headers,
            json={
                "diary_id": diary_b_id,
                "cover_image_url": "/uploads/test.png",
                "emotion_label": "neutral",
                "emotion_color": "#D3D3D3",
                "keywords": [],
                "conversation_summary": "用户B记忆"
            }
        )

        # User A sees their memories (at least 2)
        list_a = client.get("/api/v1/memories", headers=user_a_headers)
        user_a_memories = list_a.json()["data"]
        assert isinstance(user_a_memories, list)
        assert len(user_a_memories) >= 2

        # User B sees their memories (at least 1)
        list_b = client.get("/api/v1/memories", headers=user_b_headers)
        user_b_memories = list_b.json()["data"]
        assert isinstance(user_b_memories, list)
        assert len(user_b_memories) >= 1

        # Verify they don't see each other's by comparing counts
        total_memories = len(user_a_memories) + len(user_b_memories)
        assert total_memories == 3  # Should be exactly 3 total isolated memories


class TestStatsIsolation:
    """Test that stats only show current user's data."""

    def test_stats_overview_isolation(self, client):
        """Test that stats overview only shows current user's stats."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create User A with diaries
        user_a_response = client.post("/api/v1/auth/register", json={
            "username": f"stats_a_{unique_id}",
            "email": f"stats_a_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_a_headers = {"Authorization": f"Bearer {user_a_response.json()['data']['access_token']}"}

        entry_a = client.post(
            "/api/v1/entries",
            headers=user_a_headers,
            json={"raw_content": "用户A", "input_type": "text", "source_language": "zh-CN"}
        )
        entry_a_data = entry_a.json()["data"]

        client.post(
            "/api/v1/diaries",
            headers=user_a_headers,
            json={
                "entry_id": entry_a_data["id"],
                "title": "用户A",
                "content": "内容",
                "diary_date": date.today().isoformat(),
                "is_favorite": False
            }
        )

        # Create User B
        user_b_response = client.post("/api/v1/auth/register", json={
            "username": f"stats_b_{unique_id}",
            "email": f"stats_b_{unique_id}@example.com",
            "password": "Password123!"
        })
        user_b_headers = {"Authorization": f"Bearer {user_b_response.json()['data']['access_token']}"}

        # User A's stats show 1 diary
        stats_a = client.get("/api/v1/stats/overview", headers=user_a_headers)
        assert stats_a.json()["data"]["total_diaries"] == 1

        # User B's stats show 0 diaries
        stats_b = client.get("/api/v1/stats/overview", headers=user_b_headers)
        assert stats_b.json()["data"]["total_diaries"] == 0
