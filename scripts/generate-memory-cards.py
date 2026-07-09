#!/usr/bin/env python3
"""
Inner Garden Memory Cards Generator

Converts conversations into diary entries and memory cards for display in Memory Garden and Monthly Report.
Usage: python scripts/generate-memory-cards.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List
import requests

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
VPS_BASE_URL = "https://jijiayi.online"
LOCAL_BASE_URL = "http://localhost:8000"

# Use VPS by default
BASE_URL = os.getenv("BASE_URL", VPS_BASE_URL)

# Test user credentials
TEST_USER = {
    "username": "test1",
    "email": "test1@example.com",
    "password": "123456"
}

# Daily topics for June 1-29 (for title generation)
DAILY_TOPICS = [
    "今天天气不错，心情也很好",
    "工作中遇到一些小挑战，但都解决了",
    "和朋友聊了很久，感觉很放松",
    "今天读了一本有趣的书",
    "尝试了新的运动项目，很累但很开心",
    "和家人一起度过了愉快的一天",
    "学习了一个新技能，有成就感",
    "今天的状态特别好，什么都顺利",
    "遇到一些小挫折，但在调整心态",
    "周末的休闲时光，享受慢生活",
    "思考了一些人生问题，有新的感悟",
    "完成了拖延已久的任务，如释重负",
    "收到朋友的关心，心里很暖",
    "看到美丽的风景，心情愉悦",
    "今天特别想找人聊聊心事",
    "工作压力大，需要找到出口",
    "身体不舒服，在休息调整",
    "完成了重要项目，庆祝一下",
    "今天格外安静，适合反思",
    "有些焦虑，但会好起来的",
    "和朋友讨论了未来的计划",
    "今天充满正能量",
    "有些疲惫，需要休息",
    "回顾过去的经历，学到了很多",
    "今天尝试了新的爱好",
    "和朋友分享了最近的想法",
    "今天特别开心，好事连连",
    "有些失落，但在自我调节",
    "月末了，总结这个月的收获"
]

# Emotion titles for memory cards
EMOTION_TITLES = [
    "微光点亮的日子",      # happy
    "内心的宁静港湾",      # calm
    "翻涌过后是平静",      # anxious
    "雨后才有彩虹",       # sad
    "平凡中的诗意"        # neutral
]

class MemoryCardsGenerator:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.user_id = None

    def login_user(self) -> bool:
        """Login test user"""
        url = f"{self.base_url}/api/v1/auth/login"
        data = {
            "username_or_email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                self.access_token = result["data"]["access_token"]
                self.user_id = result["data"]["user"]["id"]
                print(f"✅ User logged in: {TEST_USER['username']} (ID: {self.user_id})")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def get_headers(self) -> dict:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_conversations(self) -> List:
        """Get all conversations for the user"""
        url = f"{self.base_url}/api/v1/chat/conversations"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                conversations = result["data"]["conversations"]
                print(f"  ✅ Found {len(conversations)} conversations")
                return conversations
            else:
                print(f"  ❌ Get conversations failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"  ❌ Get conversations error: {e}")
            return []

    def get_conversation_messages(self, conversation_id: int) -> List:
        """Get messages from a conversation"""
        url = f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                messages = result["data"]["messages"]
                return messages
            else:
                print(f"    ❌ Get messages failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"    ❌ Get messages error: {e}")
            return []

    def create_entry(self, content: str, conversation_id: int = None) -> dict:
        """Create an entry (returns entry with analysis)"""
        url = f"{self.base_url}/api/v1/entries"
        data = {
            "raw_content": content,
            "input_type": "text",
            "source_language": "zh-CN",
            "conversation_id": conversation_id
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            else:
                print(f"    ❌ Create entry failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"    ❌ Create entry error: {e}")
            return None

    def create_diary_from_entry(self, entry_id: int, title: str, content: str, date_str: str) -> dict:
        """Create a diary from an entry"""
        url = f"{self.base_url}/api/v1/diaries"
        data = {
            "entry_id": entry_id,
            "title": title,
            "content": content,
            "diary_date": date_str
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            elif response.status_code == 409:
                # Diary already exists, get existing diary
                print(f"      ℹ️ Diary already exists for entry {entry_id}")
                # Try to get the existing diary
                return self.get_diary_by_entry_id(entry_id)
            else:
                print(f"      ❌ Create diary failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"      ❌ Create diary error: {e}")
            return None

    def get_diary_by_entry_id(self, entry_id: int) -> dict:
        """Get diary by entry ID (for existing diaries)"""
        url = f"{self.base_url}/api/v1/diaries"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                diaries = result.get("data", [])
                for diary in diaries:
                    if diary.get("entry_id") == entry_id:
                        return diary
            return None
        except Exception as e:
            print(f"      ❌ Get diaries error: {e}")
            return None

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            else:
                print(f"    ❌ Create diary failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"    ❌ Create diary error: {e}")
            return None

    def create_memory_card(self, diary_id: int, emotion_label: str = "calm", emotion_color: str = "#8fb8ff") -> dict:
        """Create a memory card from diary"""
        url = f"{self.base_url}/api/v1/memories"
        data = {
            "diary_id": diary_id,
            "emotion_label": emotion_label,
            "emotion_color": emotion_color
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            elif response.status_code == 409:
                # Memory card already exists for this diary
                print(f"      ℹ️ Memory card already exists for diary {diary_id}")
                return None
            else:
                print(f"      ❌ Create memory card failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"      ❌ Create memory card error: {e}")
            return None

    def get_existing_memories(self) -> List:
        """Get existing memory cards"""
        url = f"{self.base_url}/api/v1/memories"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                memories = result["data"]["memories"]
                return memories
            else:
                return []
        except Exception as e:
            print(f"  ❌ Get memories error: {e}")
            return []

    def extract_user_content(self, messages: List) -> str:
        """Extract user messages from conversation"""
        user_messages = []
        for msg_wrapper in messages:
            msg = msg_wrapper.get("message", {})
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if content:
                    user_messages.append(content)

        # Join with newlines
        return "\n".join(user_messages)

    def generate_memory_cards(self):
        """Generate memory cards from conversations"""
        print(f"\n📝 Generating memory cards from conversations...")

        # Get existing memories
        existing_memories = self.get_existing_memories()
        existing_diary_ids = {m.get("diary_id") for m in existing_memories if m.get("diary_id")}
        print(f"  ℹ️ Existing memory cards: {len(existing_memories)}")

        # Get conversations
        conversations = self.get_conversations()

        # Filter conversations that don't have memory cards yet
        new_conversations = [c for c in conversations if c.get("message_count", 0) > 0]

        print(f"  📊 Processing {len(new_conversations)} conversations...")

        success_count = 0
        skip_count = 0

        for idx, conv in enumerate(new_conversations):
            conv_id = conv.get("id")
            conv_title = conv.get("title", "")

            # Extract date from title for better organization
            # Title format: "06月01日的对话" or topic text
            day_index = idx % len(DAILY_TOPICS)
            date_str = f"2026-06-{(idx + 1):02d}"

            print(f"\n  [{idx + 1}/{len(new_conversations)}] Processing: {conv_title}")

            # Get messages
            messages = self.get_conversation_messages(conv_id)
            if not messages:
                print(f"    ⚠️ No messages found, skipping")
                skip_count += 1
                continue

            # Extract user content
            user_content = self.extract_user_content(messages)
            if not user_content:
                print(f"    ⚠️ No user content found, skipping")
                skip_count += 1
                continue

            # Step 1: Create entry
            print(f"    📝 Creating entry...")
            entry_data = self.create_entry(user_content, conv_id)
            if not entry_data:
                print(f"    ⚠️ Failed to create entry, skipping")
                skip_count += 1
                continue

            entry_id = entry_data.get("id")
            print(f"    ✅ Entry created: ID {entry_id}")

            # Step 2: Create diary from entry
            # Get diary content from entry analysis
            diary_content = entry_data.get("draft_content", user_content)
            diary_title = entry_data.get("draft_title", conv_title)
            if not diary_title:
                diary_title = DAILY_TOPICS[day_index]

            print(f"      📖 Creating diary from entry...")
            diary_data = self.create_diary_from_entry(entry_id, diary_title, diary_content, date_str)
            if not diary_data:
                print(f"      ⚠️ Failed to create diary, skipping")
                skip_count += 1
                continue

            diary_id = diary_data.get("id")
            print(f"      ✅ Diary created: ID {diary_id}")

            # Check if memory card already exists
            if diary_id in existing_diary_ids:
                print(f"        ℹ️ Memory card already exists, skipping")
                skip_count += 1
                continue

            # Step 3: Generate emotion for memory card (rotate through emotions)
            emotions = ["calm", "happy", "anxious", "sad", "neutral"]
            emotion_colors = {
                "calm": "#8fb8ff",
                "happy": "#ffd93d",
                "anxious": "#ff6b6b",
                "sad": "#6bcf7f",
                "neutral": "#a8e6cf"
            }
            emotion = emotions[day_index % len(emotions)]
            emotion_color = emotion_colors.get(emotion, "#8fb8ff")

            # Create memory card
            print(f"        🎴 Creating memory card...")
            memory_data = self.create_memory_card(diary_id, emotion, emotion_color)

            if memory_data:
                memory_id = memory_data.get("id")
                print(f"      ✅ Memory card created: ID {memory_id}")
                success_count += 1
            else:
                skip_count += 1

        print(f"\n📊 Summary:")
        print(f"  ✅ Successfully created: {success_count} memory cards")
        print(f"  ⏭️ Skipped: {skip_count}")
        print(f"  📝 Total conversations: {len(new_conversations)}")

    def run(self):
        """Execute the full memory cards generation"""
        print("=" * 60)
        print("Inner Garden Memory Cards Generator")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {TEST_USER['username']} ({TEST_USER['email']})")
        print("-" * 60)

        # Step 1: Login
        if not self.login_user():
            print("❌ Failed to authenticate user")
            return False

        # Step 2: Generate memory cards
        self.generate_memory_cards()

        print("=" * 60)
        print("✅ Memory cards generation completed!")
        print("=" * 60)
        return True

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate memory cards for Inner Garden")
    parser.add_argument("--local", action="store_true", help="Use local server (localhost:8000)")
    parser.add_argument("--url", type=str, help="Custom base URL")

    args = parser.parse_args()

    if args.url:
        base_url = args.url
    elif args.local:
        base_url = LOCAL_BASE_URL
    else:
        base_url = VPS_BASE_URL

    generator = MemoryCardsGenerator(base_url)
    success = generator.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
