#!/usr/bin/env python3
"""
Inner Garden Test Data Generator

Generates test conversations and messages for a test user.
Usage: python scripts/generate-test-data.py
"""

import os
import sys
import random
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

# Daily conversation topics for June 1-29
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

# AI response templates
AI_RESPONSES = [
    "听起来你今天的状态很不错呢！能分享一下具体是什么让你感到开心吗？",
    "我理解你的感受。面对挑战时，保持积极的心态真的很重要。",
    "朋友的支持真的很珍贵。你们聊了些什么有趣的话题呢？",
    "阅读是一种很好的放松方式。这本书讲了什么内容？",
    "运动后的疲惫感其实是身体在变强的信号，坚持就会有收获！",
    "和家人在一起的时光总是温馨的。你们做了什么？",
    "学习新技能的过程很有趣也很有意义。是什么技能呢？",
    "顺顺利利的一天真好！是什么让你今天状态这么好？",
    "挫折是成长的机会，你已经在积极调整了，这很棒。",
    "慢生活让我们有时间反思和沉淀。今天有什么感悟吗？",
    "思考人生问题能帮助我们更了解自己。你有什么新的想法？",
    "完成拖延的任务后那种如释重负的感觉真好！为你高兴。",
    "朋友的关心像一缕阳光，温暖人心。他们说了什么？",
    "美丽的风景能治愈心灵。你在哪里看到了美景？",
    "我很愿意倾听你的心事。你想聊些什么？",
    "工作压力大时，找到合适的释放方式很重要。有什么我能帮你的吗？",
    "身体不舒服时，好好休息是最好的良药。希望你能早日康复。",
    "完成重要项目值得庆祝！这个项目对你有什么意义？",
    "安静的时刻适合深度思考。今天想到了什么？",
    "焦虑是正常的情绪，你已经做得很好了。慢慢来，会好起来的。",
    "和朋友的深度对话能带来新的视角。你们的讨论有什么收获？",
    "保持这种积极的状态！是什么让你充满正能量？",
    "疲惫时不要勉强自己，休息是为了走更远的路。",
    "回顾过去能帮助我们更好地面向未来。最大的收获是什么？",
    "尝试新爱好能发现生活的新乐趣。是什么爱好？",
    "分享想法能让我们梳理自己的思路。朋友们有什么反馈？",
    "好事连连的感觉真好！具体发生了什么让你这么开心？",
    "失落时允许自己感受这种情绪，但要记得相信明天会更好。",
    "月末总结很有意义。这个月你最大的收获是什么？"
]

class TestDataGenerator:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.user_id = None
        self.conversation_id = None

    def register_user(self) -> bool:
        """Register test user"""
        url = f"{self.base_url}/api/v1/auth/register"
        data = {
            "username": TEST_USER["username"],
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["data"]["access_token"]
                self.user_id = result["data"]["user"]["id"]
                print(f"✅ User registered: {TEST_USER['username']} (ID: {self.user_id})")
                return True
            elif response.status_code == 409:
                print(f"ℹ️ User already exists: {TEST_USER['username']}")
                # Try to login instead
                return self.login_user()
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    def login_user(self) -> bool:
        """Login test user"""
        url = f"{self.base_url}/api/v1/auth/login"
        data = {
            "username_or_email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
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

    def create_conversation(self, date: datetime) -> str:
        """Create a conversation for a specific date"""
        url = f"{self.base_url}/api/v1/chat/conversations"
        data = {
            "title": f"{date.strftime('%m月%d日')}的对话",
            "mode": "companion"
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                # Handle nested conversation object in response
                conversation_data = result.get("data", {})
                if "conversation" in conversation_data:
                    conversation_id = conversation_data["conversation"]["id"]
                else:
                    conversation_id = conversation_data.get("id")
                print(f"  ✅ Created conversation: {data['title']} (ID: {conversation_id})")
                return conversation_id
            else:
                print(f"  ❌ Create conversation failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"  ❌ Create conversation error: {e}")
            return None

    def send_message(self, conversation_id: str, content: str, is_user: bool = True) -> bool:
        """Send a message to conversation"""
        url = f"{self.base_url}/api/v1/chat/messages"
        data = {
            "conversation_id": conversation_id,
            "content": content,
            "role": "user" if is_user else "assistant"
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=30)
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"    ❌ Send message failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"    ❌ Send message error: {e}")
            return False

    def generate_conversations_for_june(self):
        """Generate conversations for each day in June 1-29"""
        print(f"\n📝 Generating conversations for June 1-29, 2026...")

        # Start from June 1, 2026
        start_date = datetime(2026, 6, 1)

        for day in range(29):  # June 1-29
            current_date = start_date + timedelta(days=day)

            # Create conversation for this day
            conversation_id = self.create_conversation(current_date)
            if not conversation_id:
                continue

            # Generate 2-4 message exchanges for this day
            num_exchanges = random.randint(2, 4)

            # Get daily topic
            user_message = DAILY_TOPICS[day % len(DAILY_TOPICS)]

            for exchange in range(num_exchanges):
                # User message (with variation)
                if exchange == 0:
                    user_msg = user_message
                else:
                    # Follow-up messages
                    follow_ups = [
                        "对，就是这样",
                        "我觉得很有道理",
                        "让我想想",
                        "确实如此",
                        "嗯，我同意",
                        "再详细说说"
                    ]
                    user_msg = random.choice(follow_ups)

                # Send user message
                if not self.send_message(conversation_id, user_msg, is_user=True):
                    continue

                # AI response
                ai_response = AI_RESPONSES[day % len(AI_RESPONSES)]
                if not self.send_message(conversation_id, ai_response, is_user=False):
                    continue

            print(f"    ✅ Added {num_exchanges} message exchanges for {current_date.strftime('%m-%d')}")

    def run(self):
        """Execute the full test data generation"""
        print("=" * 60)
        print("Inner Garden Test Data Generator")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {TEST_USER['username']} ({TEST_USER['email']})")
        print("-" * 60)

        # Step 1: Register/Login
        if not self.register_user():
            if not self.login_user():
                print("❌ Failed to authenticate user")
                return False

        # Step 2: Generate conversations
        self.generate_conversations_for_june()

        print("=" * 60)
        print("✅ Test data generation completed!")
        print(f"User: {TEST_USER['username']}")
        print(f"Generated: 29 daily conversations (June 1-29)")
        print("=" * 60)
        return True

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test data for Inner Garden")
    parser.add_argument("--local", action="store_true", help="Use local server (localhost:8000)")
    parser.add_argument("--url", type=str, help="Custom base URL")

    args = parser.parse_args()

    if args.url:
        base_url = args.url
    elif args.local:
        base_url = LOCAL_BASE_URL
    else:
        base_url = VPS_BASE_URL

    generator = TestDataGenerator(base_url)
    success = generator.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
