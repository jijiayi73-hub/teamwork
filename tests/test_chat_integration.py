"""Integration test for Chat API with Deepseek.

This test creates a user, sends a chat message, and verifies the response.
"""
import sys
import os
from pathlib import Path
import requests
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

API_BASE = "http://localhost:8000/api/v1"

def test_chat_api():
    """Test the chat API with Deepseek."""
    print("=" * 60)
    print("Testing Chat API with Deepseek")
    print("=" * 60)

    # Step 1: Login as test user
    print("\n1. Logging in as test user...")
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": "deepseek_test", "password": "test123"}
    )

    if login_response.status_code != 200:
        print(f"   Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return False

    login_data = login_response.json()
    token = login_data["data"]["access_token"]
    user_id = login_data["data"]["user"]["id"]
    print(f"   Logged in as user {user_id}")

    # Step 2: Send chat message
    print("\n2. Sending chat message to Deepseek...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    chat_request = {
        "content": "你好！请用一句话介绍一下你自己。",
        "mode": "companion",
        "use_memory": False
    }

    print(f"   Request: {chat_request}")

    chat_response = requests.post(
        f"{API_BASE}/chat/messages",
        headers=headers,
        json=chat_request
    )

    print(f"   Response status: {chat_response.status_code}")

    if chat_response.status_code != 200:
        print(f"   Chat API failed: {chat_response.status_code}")
        print(f"   Response: {chat_response.text}")
        return False

    # Step 3: Verify response
    print("\n3. Verifying response...")
    response_data = chat_response.json()

    if not response_data.get("success"):
        print(f"   API returned success=False")
        print(f"   Message: {response_data.get('message')}")
        return False

    data = response_data.get("data", {})
    user_message = data.get("user_message", {})
    assistant_message = data.get("assistant_message", {})

    print(f"\n   User message: {user_message.get('content', 'N/A')}")
    print(f"   Assistant response: {assistant_message.get('content', 'N/A')}")
    print(f"   Message ID: {assistant_message.get('id', 'N/A')}")
    print(f"   Created at: {assistant_message.get('created_at', 'N/A')}")

    # Verify conversation metadata
    conversation = data.get("conversation", {})
    print(f"   Conversation ID: {conversation.get('id', 'N/A')}")
    print(f"   Conversation mode: {conversation.get('mode', 'N/A')}")

    print("\n" + "=" * 60)
    print("Chat API Test Completed Successfully!")
    print("=" * 60)
    return True


def test_health_check():
    """Test health check endpoint."""
    print("\nTesting health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


if __name__ == "__main__":
    # First check if server is running
    if not test_health_check():
        print("\nServer is not running. Please start the server first:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        sys.exit(1)

    # Run chat API test
    if test_chat_api():
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)
