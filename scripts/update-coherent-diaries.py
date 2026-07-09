#!/usr/bin/env python3
"""
Inner Garden Coherent Diary Content Updater

Updates existing diary entries with coherent temporal narratives.
This script replaces generic fallback content with rich, logically connected stories.

Usage: python scripts/update-coherent-diaries.py [--local] [--url URL]
"""

import os
import sys
import json
from datetime import datetime
import requests

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
VPS_BASE_URL = "https://jijiayi.online"
LOCAL_BASE_URL = "http://localhost:8000"

BASE_URL = os.getenv("BASE_URL", VPS_BASE_URL)

# Test user credentials
TEST_USER = {
    "username": "test1",
    "email": "test1@example.com",
    "password": "123456"
}

# Coherent content for dates that need updating
# These are the dates that have generic content and need to be replaced
COHERENT_UPDATES = {
    "2026-06-01": {
        "title": "六月的新开始",
        "content": "六月的第一天，站在公司落地窗前看着城市苏醒。领导今天找我谈话，提到了一个新的AI项目——智能客服系统升级，问我是否有兴趣牵头。我心里既兴奋又紧张，这是难得的机会，也意味着巨大的挑战。晚上回家时经过书店，买了一本关于机器学习实战的书，打算这个月好好充电。",
        "emotion": "anxious"
    },
    "2026-06-02": {
        "title": "认真考虑后的决定",
        "content": "昨晚几乎没睡好，脑子里一直在想那个项目。今天早上给爸爸打了电话，他说人生难得遇到几个真正能改变轨迹的机会，让我勇敢去尝试。这句话给了我很大勇气。下午我正式回复领导，接下了这个项目。团队里有五个人，需要协调跨部门合作，压力不小。晚上开始看那本书的前两章，有些概念还需要消化。",
        "emotion": "anxious"
    },
    "2026-06-03": {
        "title": "第一次项目会议",
        "content": "今天开了项目的kickoff meeting。认识了团队成员：产品经理小陈、技术负责人老张、算法工程师小李，还有一个新来的实习生小王。会议确定了里程碑——七月底要完成MVP版本。时间很紧，但大家的斗志都很高。老张说这个项目如果成功，可能会推广到整个集团的客服系统，影响很大。散会时小李提议周末一起吃个饭增进了解，我答应了。",
        "emotion": "neutral"
    },
    "2026-06-04": {
        "title": "技术调研开始",
        "content": "小李今天带我看了现有的客服系统架构，问题很多：响应慢、准确率低、用户反馈差。我们需要重构整个对话引擎。下午查阅了很多论文，关于RAG和强化学习在对话系统中的应用。晚上在技术论坛看到一篇很有启发的文章，收藏起来明天仔细研究。感觉这个项目比我想象的复杂，但越有挑战越有价值。",
        "emotion": "neutral"
    },
    "2026-06-05": {
        "title": "图书馆的偶遇",
        "content": "周末去了市图书馆想安静地看会儿书，竟然在机器学习区遇到了昨天那篇论坛文章的作者——一个叫林月的女孩子。她正在写关于对话系统的论文，我们聊了很久，发现很多想法不谋而合。她提到一个很创新的思路：用时间序列建模来追踪用户情绪变化。这个点子让我很兴奋，或许可以用到我们的项目中。我们约定下周再讨论。",
        "emotion": "happy"
    },
    "2026-06-06": {
        "title": "健身房的决心",
        "content": "项目压力大，感觉身体跟不上。今天终于下定决心办了健身卡。教练小李说我基础不错，但需要坚持。第一次训练累得半死，但出汗的感觉很好。从小白那里得知，身体状态直接影响工作效率，这个项目可能会经常加班，必须强健体魄。计划每周去三次，先坚持一个月再说。",
        "emotion": "neutral"
    },
    "2026-06-07": {
        "title": "和林月的深度讨论",
        "content": "今天和林月约在咖啡店讨论她的情绪追踪模型。她用图神经网络来表示用户对话历史中的实体关系，这个方法很有创意。我们讨论了很久，她同意作为项目的学术顾问参与进来。能找到一个志同道合的人，感觉这个项目更有希望了。晚上回到家，脑子里还满是她的想法，在笔记本上画了好多架构草图。",
        "emotion": "happy"
    },
    "2026-06-08": {
        "title": "向团队介绍新思路",
        "content": "在今天的团队会议上，我向老张和小李介绍了林月的情绪追踪模型。老张一开始有些怀疑，担心技术风险，但在看到具体实现方案后，态度软化了很多。小李则非常兴奋，说这正是他一直在找的突破点。我们决定先做一个小的POC验证可行性。会后老张单独找我，说看到我这么投入，他也被带动起来了。团队氛围越来越好。",
        "emotion": "happy"
    },
    "2026-06-09": {
        "title": "妈妈的担忧",
        "content": "给妈妈打电话汇报最近的工作，她听说了我要负责大项目，既为我高兴又担心我的身体。她说爸爸最近血压有点高，但她没让爸爸告诉我，怕我分心。挂了电话心里有些酸涩。工作很重要，但家人的健康更不能忽视。计划下周抽时间回家看看。晚上加班时，给自己定了个规矩：不管多忙，每周至少给家里打两次电话。",
        "emotion": "anxious"
    },
    "2026-06-10": {
        "title": "POC开发的挑战",
        "content": "小李和我开始做POC，遇到了不少技术难题。情绪模型的训练需要大量标注数据，但我们没有现成的数据集。林月建议用合成数据先训练一个基础版本，然后再用真实数据fine-tune。这个思路可行，但生成高质量合成数据本身就是个挑战。今天调试代码到晚上九点，才勉强跑通第一个模型。性能还不行，但框架已经搭起来了。",
        "emotion": "neutral"
    },
    "2026-06-11": {
        "title": "健身房的小进步",
        "content": "第二次去健身房，教练说我动作标准多了。今天尝试了器械训练，虽然重量不大，但能感觉到肌肉在发力。健身真的很神奇，运动完整个人神清气爽，之前写代码时的疲惫感一扫而空。决定以后每次遇到技术难题卡壳时，就来健身房发泄一下。这里渐渐成了我的避风港。",
        "emotion": "calm"
    },
    "2026-06-12": {
        "title": "第一次和团队聚餐",
        "content": "小李提议的聚餐终于成行了。我们去了家川菜馆，大家喝了一点啤酒，聊了很多工作外的话题。小陈原来是个游戏迷，老张喜欢钓鱼，小李在学摄影。我发现放下工作的大家都是很有趣的人。席间老张说起他年轻时负责的第一个项目，失败了，但那次经历让他学会了什么是真正的坚持。这个故事给了我很多启发。",
        "emotion": "happy"
    },
    "2026-06-13": {
        "title": "回家看父母",
        "content": "今天抽空回家了一趟，爸爸看起来气色不错，妈妈做了一桌我爱吃的菜。爸爸给我看了他的体检报告，医生说只要注意饮食和运动，血压问题不难控制。我陪爸爸去公园散步，他讲了好多他年轻时的故事。那一刻突然意识到，父母正在以自己的方式慢慢老去，而我能做的就是多陪陪他们。回程的路上，心里暖暖的。",
        "emotion": "calm"
    },
    "2026-06-14": {
        "title": "模型性能瓶颈",
        "content": "POC运行了一周，结果不如预期。情绪识别的准确率只有65%，远远达不到生产要求。小李和我分析了一整天，发现是数据质量问题——合成数据和真实用户表达差距太大。林月建议我们尝试迁移学习，用更大的预训练模型。这个方向可行，但意味着要调整整个技术路线。需要向团队汇报这个坏消息，心情很沉重。",
        "emotion": "anxious"
    },
    "2026-06-16": {
        "title": "林月的灵感",
        "content": "和林月开了三个小时的视频会，她提出了一个大胆的想法：不用通用模型，而是针对特定场景训练小模型。虽然单一模型能力弱，但多个小模型组合起来，效果可能更好。这个思路很有启发性，我们决定选三个典型客服场景做验证。晚上躺在床上，脑子里全是模型架构图，兴奋得睡不着。好久没有这种技术狂热的感觉了。",
        "emotion": "happy"
    },
    "2026-06-17": {
        "title": "新的技术方案",
        "content": "把新方案整理成文档，在内部评审会上汇报。领导一开始有疑虑，但在看到详细的实现路径和预期收益后，同意我们调整方向。老张说要给我记一功，我说这是大家一起的功劳。散会时已经是晚上八点，小李提议去吃夜宵庆祝。坐在烧烤摊前，看着烟雾缭绕，突然觉得这种为梦想拼搏的感觉真好。",
        "emotion": "happy"
    },
    "2026-06-18": {
        "title": "健身房的瓶颈期",
        "content": "这周去健身房感觉进步不明显，教练说这是正常现象，身体在适应新的训练强度。他建议我增加有氧运动，还要注意休息。仔细想想，其实工作和健身一样，都会遇到瓶颈期。现在技术上遇到困难，不也是一种瓶颈吗？突破之后，就会进入新的阶段。今晚拉伸时，突然想明白了一些事情。",
        "emotion": "neutral"
    },
    "2026-06-19": {
        "title": "爸爸的生日",
        "content": "今天是爸爸的生日，特意请了半天假回家。一家人围坐在餐桌前，妈妈做了长寿面。爸爸说今年收到的最好的生日礼物就是我能够常常回家。看着爸妈的笑容，心里暖暖的，又有一丝愧疚。这段时间工作太忙，陪伴他们的时间太少。许愿时，我默默祈祷家人身体健康，也希望这个项目能够成功，让他们为我骄傲。",
        "emotion": "calm"
    },
    "2026-06-20": {
        "title": "项目进展汇报",
        "content": "向领导汇报项目进展。虽然还没有可展示的成果，但新的技术路线得到了认可。领导说这个项目如果成功，不仅对公司有重大意义，对我们每个人的职业生涯都是加分项。他提到公司下半年可能会组织技术峰会，建议我们把项目经验整理成论文。这个提议让我很心动，毕竟能在技术峰会分享是很多工程师的梦想。",
        "emotion": "neutral"
    }
}

# Emotion mappings
EMOTION_COLORS = {
    "happy": "#ffd93d",
    "calm": "#8fb8ff",
    "anxious": "#ff6b6b",
    "sad": "#6bcf7f",
    "neutral": "#a8e6cf",
    "疲惫": "#c9b1ff",
    "怀念": "#ffb4e6"
}

EMOTION_LABELS = {
    "happy": "开心",
    "calm": "平静",
    "anxious": "焦虑",
    "sad": "难过",
    "neutral": "中性",
    "疲惫": "疲惫",
    "怀念": "怀念"
}


class DiaryUpdater:
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

    def get_all_diaries(self) -> list:
        """Get all diaries"""
        url = f"{self.base_url}/api/v1/diaries"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            return []
        except Exception as e:
            print(f"  ❌ Get diaries error: {e}")
            return []

    def get_diary_by_date(self, date_str: str) -> dict:
        """Get diary by date"""
        diaries = self.get_all_diaries()
        for d in diaries:
            if d.get("diary_date") == date_str:
                return d
        return None

    def update_diary(self, diary_id: int, title: str, content: str) -> bool:
        """Update diary content"""
        url = f"{self.base_url}/api/v1/diaries/{diary_id}"
        data = {
            "title": title,
            "content": content
        }

        try:
            response = requests.patch(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"      ❌ Update diary failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"      ❌ Update diary error: {e}")
            return False

    def get_memory_by_diary_id(self, diary_id: int) -> dict:
        """Get memory card by diary ID"""
        url = f"{self.base_url}/api/v1/memories"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                memories = result["data"]
                for m in memories:
                    if m.get("diary_id") == diary_id:
                        return m
            return None
        except Exception as e:
            print(f"      ❌ Get memory error: {e}")
            return None

    def update_memory_emotion(self, memory_id: int, emotion: str, keywords: list) -> bool:
        """Update memory card emotion and keywords"""
        url = f"{self.base_url}/api/v1/memories/{memory_id}"
        emotion_label = EMOTION_LABELS.get(emotion, "平静")
        emotion_color = EMOTION_COLORS.get(emotion, "#8fb8ff")

        data = {
            "emotion_label": emotion_label,
            "emotion_color": emotion_color,
            "keywords": keywords  # Use 'keywords' not 'keywords_json'
        }

        try:
            response = requests.patch(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"        ❌ Update memory failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"        ❌ Update memory error: {e}")
            return False

    def update_diaries(self):
        """Update diaries with coherent content"""
        print(f"\n📝 Updating diaries with coherent narratives...")
        print(f"📖 Target dates: {len(COHERENT_UPDATES)} entries")
        print()

        success_count = 0
        skip_count = 0
        error_count = 0

        for date_str, update_data in COHERENT_UPDATES.items():
            title = update_data["title"]
            content = update_data["content"]
            emotion = update_data.get("emotion", "neutral")
            keywords = update_data.get("keywords", [])

            print(f"  📅 {date_str} - {title}")

            # Get existing diary
            diary = self.get_diary_by_date(date_str)
            if not diary:
                print(f"    ⚠️  No diary found for this date, skipping")
                skip_count += 1
                continue

            diary_id = diary.get("id")

            # Update diary content
            if self.update_diary(diary_id, title, content):
                print(f"    ✅ Diary updated: ID {diary_id}")
            else:
                print(f"    ❌ Failed to update diary")
                error_count += 1
                continue

            # Get and update memory card
            memory = self.get_memory_by_diary_id(diary_id)
            if memory:
                memory_id = memory.get("id")
                if self.update_memory_emotion(memory_id, emotion, keywords):
                    print(f"    ✅ Memory updated: ID {memory_id}")
                    success_count += 1
                else:
                    print(f"    ⚠️  Memory update failed (diary was updated)")
                    success_count += 1
            else:
                print(f"    ℹ️  No memory card found (diary was updated)")
                success_count += 1

            print()

        print(f"📊 Summary:")
        print(f"  ✅ Successfully updated: {success_count} diaries")
        print(f"  ⏭️  Skipped: {skip_count}")
        print(f"  ❌ Errors: {error_count}")

    def run(self):
        """Execute the diary update"""
        print("=" * 60)
        print("Inner Garden Coherent Diary Updater")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {TEST_USER['username']} ({TEST_USER['email']})")
        print("-" * 60)

        # Step 1: Login
        if not self.login_user():
            print("❌ Failed to authenticate user")
            return False

        # Step 2: Update diaries
        self.update_diaries()

        print("=" * 60)
        print("✅ Diary update completed!")
        print("=" * 60)
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Update diaries with coherent content")
    parser.add_argument("--local", action="store_true", help="Use local server (localhost:8000)")
    parser.add_argument("--url", type=str, help="Custom base URL")

    args = parser.parse_args()

    if args.url:
        base_url = args.url
    elif args.local:
        base_url = LOCAL_BASE_URL
    else:
        base_url = VPS_BASE_URL

    updater = DiaryUpdater(base_url)
    success = updater.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
