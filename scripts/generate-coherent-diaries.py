#!/usr/bin/env python3
"""
Inner Garden Coherent Diary Content Generator

Generates diary entries with logical temporal coherence for time-series RAG testing.
The content follows several narrative threads that develop over June 2026:

1. Work Project Journey - A major project at work from initiation to completion
2. Personal Growth - Learning new skills and self-improvement
3. Relationship - Building a friendship/relationship
4. Health Journey - Fitness and wellness goals
5. Family Events - Family gatherings and milestones

Each day's content references previous days and sets up future events,
creating a rich temporal graph for RAG testing.

Usage: python scripts/generate-coherent-diaries.py [--local] [--url URL]
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

BASE_URL = os.getenv("BASE_URL", VPS_BASE_URL)

# Test user credentials
TEST_USER = {
    "username": "test1",
    "email": "test1@example.com",
    "password": "123456"
}

# Coherent daily diary content for June 2026
# Each entry builds on previous days with references and foreshadowing
COHERENT_DIARIES = {
    # Week 1: June 1-6 - Project Initiation & New Beginnings
    "2026-06-01": {
        "title": "六月的新开始",
        "content": "六月的第一天，站在公司落地窗前看着城市苏醒。领导今天找我谈话，提到了一个新的AI项目——智能客服系统升级，问我是否有兴趣牵头。我心里既兴奋又紧张，这是难得的机会，也意味着巨大的挑战。晚上回家时经过书店，买了一本关于机器学习实战的书，打算这个月好好充电。",
        "emotion": "anxious",
        "keywords": ["新项目", "AI", "机会", "挑战", "学习"]
    },
    "2026-06-02": {
        "title": "认真考虑后的决定",
        "content": "昨晚几乎没睡好，脑子里一直在想那个项目。今天早上给爸爸打了电话，他说人生难得遇到几个真正能改变轨迹的机会，让我勇敢去尝试。这句话给了我很大勇气。下午我正式回复领导，接下了这个项目。团队里有五个人，需要协调跨部门合作，压力不小。晚上开始看那本书的前两章，有些概念还需要消化。",
        "emotion": "anxious",
        "keywords": ["决定", "爸爸", "勇气", "团队", "学习"]
    },
    "2026-06-03": {
        "title": "第一次项目会议",
        "content": "今天开了项目的kickoff meeting。认识了团队成员：产品经理小陈、技术负责人老张、算法工程师小李，还有一个新来的实习生小王。会议确定了里程碑——七月底要完成MVP版本。时间很紧，但大家的斗志都很高。老张说这个项目如果成功，可能会推广到整个集团的客服系统，影响很大。散会时小李提议周末一起吃个饭增进了解，我答应了。",
        "emotion": "neutral",
        "keywords": ["会议", "团队", "里程碑", "目标", "聚餐"]
    },
    "2026-06-04": {
        "title": "技术调研开始",
        "content": "小李今天带我看了现有的客服系统架构，问题很多：响应慢、准确率低、用户反馈差。我们需要重构整个对话引擎。下午查阅了很多论文，关于RAG和强化学习在对话系统中的应用。晚上在技术论坛看到一篇很有启发的文章，收藏起来明天仔细研究。感觉这个项目比我想象的复杂，但越有挑战越有价值。",
        "emotion": "neutral",
        "keywords": ["技术", "调研", "架构", "学习", "挑战"]
    },
    "2026-06-05": {
        "title": "图书馆的偶遇",
        "content": "周末去了市图书馆想安静地看会儿书，竟然在机器学习区遇到了昨天那篇论坛文章的作者——一个叫林月的女孩子。她正在写关于对话系统的论文，我们聊了很久，发现很多想法不谋而合。她提到一个很创新的思路：用时间序列建模来追踪用户情绪变化。这个点子让我很兴奋，或许可以用到我们的项目中。我们约定下周再讨论。",
        "emotion": "happy",
        "keywords": ["图书馆", "偶遇", "林月", "灵感", "合作"]
    },
    "2026-06-06": {
        "title": "健身房的决心",
        "content": "项目压力大，感觉身体跟不上。今天终于下定决心办了健身卡。教练小李说我基础不错，但需要坚持。第一次训练累得半死，但出汗的感觉很好。从小白那里得知，身体状态直接影响工作效率，这个项目可能会经常加班，必须强健体魄。计划每周去三次，先坚持一个月再说。",
        "emotion": "neutral",
        "keywords": ["健身", "健康", "压力", "坚持", "计划"]
    },

    # Week 2: June 7-13 - Deep Dive & Connections
    "2026-06-07": {
        "title": "和林月的深度讨论",
        "content": "今天和林月约在咖啡店讨论她的情绪追踪模型。她用图神经网络来表示用户对话历史中的实体关系，这个方法很有创意。我们讨论了很久，她同意作为项目的学术顾问参与进来。能找到一个志同道合的人，感觉这个项目更有希望了。晚上回到家，脑子里还满是她的想法，在笔记本上画了好多架构草图。",
        "emotion": "happy",
        "keywords": ["林月", "讨论", "模型", "顾问", "灵感"]
    },
    "2026-06-08": {
        "title": "向团队介绍新思路",
        "content": "在今天的团队会议上，我向老张和小李介绍了林月的情绪追踪模型。老张一开始有些怀疑，担心技术风险，但在看到具体实现方案后，态度软化了很多。小李则非常兴奋，说这正是他一直在找的突破点。我们决定先做一个小的POC验证可行性。会后老张单独找我，说看到我这么投入，他也被带动起来了。团队氛围越来越好。",
        "emotion": "happy",
        "keywords": ["团队", "模型", "说服", "进展", "氛围"]
    },
    "2026-06-09": {
        "title": "妈妈的担忧",
        "content": "给妈妈打电话汇报最近的工作，她听说了我要负责大项目，既为我高兴又担心我的身体。她说爸爸最近血压有点高，但她没让爸爸告诉我，怕我分心。挂了电话心里有些酸涩。工作很重要，但家人的健康更不能忽视。计划下周抽时间回家看看。晚上加班时，给自己定了个规矩：不管多忙，每周至少给家里打两次电话。",
        "emotion": "anxious",
        "keywords": ["妈妈", "家人", "健康", "愧疚", "平衡"]
    },
    "2026-06-10": {
        "title": "POC开发的挑战",
        "content": "小李和我开始做POC，遇到了不少技术难题。情绪模型的训练需要大量标注数据，但我们没有现成的数据集。林月建议用合成数据先训练一个基础版本，然后再用真实数据fine-tune。这个思路可行，但生成高质量合成数据本身就是个挑战。今天调试代码到晚上九点，才勉强跑通第一个模型。性能还不行，但框架已经搭起来了。",
        "emotion": "neutral",
        "keywords": ["POC", "开发", "挑战", "数据", "进展"]
    },
    "2026-06-11": {
        "title": "健身房的小进步",
        "content": "第二次去健身房，教练说我动作标准多了。今天尝试了器械训练，虽然重量不大，但能感觉到肌肉在发力。健身真的很神奇，运动完整个人神清气爽，之前写代码时的疲惫感一扫而空。决定以后每次遇到技术难题卡壳时，就来健身房发泄一下。这里渐渐成了我的避风港。",
        "emotion": "calm",
        "keywords": ["健身", "进步", "放松", "解压", "习惯"]
    },
    "2026-06-12": {
        "title": "第一次和团队聚餐",
        "content": "小李提议的聚餐终于成行了。我们去了家川菜馆，大家喝了一点啤酒，聊了很多工作外的话题。小陈原来是个游戏迷，老张喜欢钓鱼，小李在学摄影。我发现放下工作的大家都是很有趣的人。席间老张说起他年轻时负责的第一个项目，失败了，但那次经历让他学会了什么是真正的坚持。这个故事给了我很多启发。",
        "emotion": "happy",
        "keywords": ["聚餐", "团队", "交流", "故事", "启发"]
    },
    "2026-06-13": {
        "title": "回家看父母",
        "content": "今天抽空回家了一趟，爸爸看起来气色不错，妈妈做了一桌我爱吃的菜。爸爸给我看了他的体检报告，医生说只要注意饮食和运动，血压问题不难控制。我陪爸爸去公园散步，他讲了好多他年轻时的故事。那一刻突然意识到，父母正在以自己的方式慢慢老去，而我能做的就是多陪陪他们。回程的路上，心里暖暖的。",
        "emotion": "calm",
        "keywords": ["家人", "父母", "陪伴", "温暖", "感悟"]
    },

    # Week 3: June 14-20 - Setbacks & Breakthroughs
    "2026-06-14": {
        "title": "模型性能瓶颈",
        "content": "POC运行了一周，结果不如预期。情绪识别的准确率只有65%，远远达不到生产要求。小李和我分析了一整天，发现是数据质量问题——合成数据和真实用户表达差距太大。林月建议我们尝试迁移学习，用更大的预训练模型。这个方向可行，但意味着要调整整个技术路线。需要向团队汇报这个坏消息，心情很沉重。",
        "emotion": "anxious",
        "keywords": ["模型", "瓶颈", "数据", "技术路线", "挫折"]
    },
    "2026-06-15": {
        "title": "团队的支持",
        "content": "今天的会议我如实汇报了POC的问题。本以为会被质疑，但老张第一个站出来支持调整技术路线，说创新哪有一帆风顺的。小陈提议延长第一阶段的交付时间，小李立刻说愿意加班赶进度。听到这些话，鼻子有点酸。这就是团队的意义吧——不是一起成功，而是一起面对失败。会后林月发来消息，说她那边有些新的想法，或许能帮助我们。",
        "emotion": "calm",
        "keywords": ["团队", "支持", "挫折", "温暖", "合作"]
    },
    "2026-06-16": {
        "title": "林月的灵感",
        "content": "和林月开了三个小时的视频会，她提出了一个大胆的想法：不用通用模型，而是针对特定场景训练小模型。虽然单一模型能力弱，但多个小模型组合起来，效果可能更好。这个思路很有启发性，我们决定选三个典型客服场景做验证。晚上躺在床上，脑子里全是模型架构图，兴奋得睡不着。好久没有这种技术狂热的感觉了。",
        "emotion": "happy",
        "keywords": ["林月", "灵感", "模型", "创新", "兴奋"]
    },
    "2026-06-17": {
        "title": "新的技术方案",
        "content": "把新方案整理成文档，在内部评审会上汇报。领导一开始有疑虑，但在看到详细的实现路径和预期收益后，同意我们调整方向。老张说要给我记一功，我说这是大家一起的功劳。散会时已经是晚上八点，小李提议去吃夜宵庆祝。坐在烧烤摊前，看着烟雾缭绕，突然觉得这种为梦想拼搏的感觉真好。",
        "emotion": "happy",
        "keywords": ["方案", "通过", "团队", "庆祝", "拼搏"]
    },
    "2026-06-18": {
        "title": "健身房的瓶颈期",
        "content": "这周去健身房感觉进步不明显，教练说这是正常现象，身体在适应新的训练强度。他建议我增加有氧运动，还要注意休息。仔细想想，其实工作和健身一样，都会遇到瓶颈期。现在技术上遇到困难，不也是一种瓶颈吗？突破之后，就会进入新的阶段。今晚拉伸时，突然想明白了一些事情。",
        "emotion": "neutral",
        "keywords": ["健身", "瓶颈", "适应", "领悟", "成长"]
    },
    "2026-06-19": {
        "content": "今天是爸爸的生日，特意请了半天假回家。一家人围坐在餐桌前，妈妈做了长寿面。爸爸说今年收到的最好的生日礼物就是我能够常常回家。看着爸妈的笑容，心里暖暖的，又有一丝愧疚。这段时间工作太忙，陪伴他们的时间太少。许愿时，我默默祈祷家人身体健康，也希望这个项目能够成功，让他们为我骄傲。",
        "title": "爸爸的生日",
        "emotion": "calm",
        "keywords": ["爸爸", "生日", "家人", "陪伴", "愿望"]
    },
    "2026-06-20": {
        "title": "项目进展汇报",
        "content": "向领导汇报项目进展。虽然还没有可展示的成果，但新的技术路线得到了认可。领导说这个项目如果成功，不仅对公司有重大意义，对我们每个人的职业生涯都是加分项。他提到公司下半年可能会组织技术峰会，建议我们把项目经验整理成论文。这个提议让我很心动，毕竟能在技术峰会分享是很多工程师的梦想。",
        "emotion": "neutral",
        "keywords": ["汇报", "进展", "认可", "峰会", "目标"]
    },

    # Week 4: June 21-27 - Acceleration & Reflection
    "2026-06-21": {
        "title": "夏至日的思考",
        "content": "今天是夏至，一年中白天最长的一天。下班时天还大亮，走路回家时在想，时间过得真快，六月已经过去三分之二了。这二十一天里，经历了项目的起伏，认识了林月这样的朋友，重新开始健身，也花更多时间陪伴家人。生活好像比以前丰富了很多。或许这就是成长的意义——在挑战中发现新的可能性。",
        "emotion": "calm",
        "keywords": ["夏至", "时间", "成长", "反思", "生活"]
    },
    "2026-06-22": {
        "title": "小模型方案启动",
        "content": "三个场景的小模型开发正式启动。我负责订单咨询场景，小李负责产品问答，老张带着小王做技术支持。林月虽然在外地，但每天都会参与我们的线上讨论。这种分布式协作的感觉很奇妙，地理位置不重要，重要的是共同的目标。今天完成了第一个小模型的初步训练，准确率达到78%，比之前好很多。",
        "emotion": "happy",
        "keywords": ["开发", "小模型", "协作", "进展", "准确率"]
    },
    "2026-06-23": {
        "title": "健身房的新朋友",
        "content": "在健身房认识了一个新朋友阿杰，是个程序员，在另一家互联网公司工作。我们聊起各自的项目，发现他也在做AI相关的开发。他告诉我他们公司最近在招聘，暗示我如果有兴趣可以聊聊。我婉拒了，但心里有些触动——才一个月前还在为找不到方向焦虑，现在却有了选择。这大概就是能力被认可的感觉吧。",
        "emotion": "neutral",
        "keywords": ["健身房", "朋友", "机会", "认可", "选择"]
    },
    "2026-06-24": {
        "title": "妈妈的电话",
        "content": "妈妈打电话来说，她最近参加了社区的老年大学，学摄影和书法。她兴奋地给我看她拍的照片和写的毛笔字，真的进步很大。听她这么开心，我也很欣慰。父母也需要自己的生活，不能把所有注意力都放在子女身上。挂电话前她说，看到我这么努力，她也在努力过好自己的生活，不想成为我的负担。那一刻，眼泪差点掉下来。",
        "emotion": "calm",
        "keywords": ["妈妈", "老年大学", "生活", "欣慰", "感动"]
    },
    "2026-06-25": {
        "title": "三模型集成测试",
        "content": "今天是个重要的日子——三个小模型第一次联合测试。结果还算可以，整体准确率达到82%，虽然还有改进空间，但已经能看到方向了。老张说接下来要优化模型间的协调机制，小李提议加一个元模型做任务分发。大家讨论了很久，最终决定先用规则引擎，等有足够数据再训练元模型。工程上要做很多trade-off，这就是现实。",
        "emotion": "neutral",
        "keywords": ["测试", "集成", "准确率", "优化", "决策"]
    },
    "2026-06-26": {
        "title": "林月的论文邀请",
        "content": "林月今天告诉我，她的论文被ACL录用了，问我是否有兴趣作为合作作者署名。这是个很意外的惊喜，ACL是NLP领域的顶级会议。她说我们的项目实践为论文提供了很好的实验数据，这个合作是双赢的。激动之余也有些压力，这意味着我们的工作要接受国际同行的审视。但这正是一个证明自己的机会。",
        "emotion": "happy",
        "keywords": ["林月", "论文", "ACL", "合作", "机会"]
    },
    "2026-06-27": {
        "title": "月末总结",
        "content": "六月快结束了，整理这个月的笔记，竟然写满了大半个本子。从项目启动到现在，经历了技术方案的调整、团队的磨合、个人的成长。健身坚持了将近一个月，体重降了三公斤，但更重要的是精神状态的变化。林月成了很好的合作伙伴，也或许会是朋友。爸妈的身体状况稳定，他们也在过着自己的生活。一切都在向好的方向发展。",
        "emotion": "calm",
        "keywords": ["总结", "成长", "项目", "健身", "家人"]
    },

    # Final days: June 28-29
    "2026-06-28": {
        "title": "为七月做准备",
        "content": "明天就是六月最后一天了，今天团队开了个会，规划七月的工作重点。MVP版本定在7月25日上线，时间很紧但大家信心满满。小李说要做个demo给领导展示，老张在考虑部署方案，小陈在准备用户调研。我负责整体协调，还要开始准备技术峰会的材料。七月注定是更忙碌的一个月，但有了六月的铺垫，我相信我们能做到。",
        "emotion": "neutral",
        "keywords": ["计划", "七月", "MVP", "团队", "准备"]
    },
    "2026-06-29": {
        "title": "六月的最后一天",
        "content": "六月最后一天，下班时特意在公司楼下的咖啡店坐了一会儿。回想这一个月，从一个担心能否胜任的职场人，变成带领团队冲刺的项目负责人。认识了林月这样的学术伙伴，重新捡起健身的习惯，更懂得陪伴家人的重要。明天就是七月了，新的挑战在等待。但此刻，我想好好感谢这个六月——它让我看到了更广阔的可能性，也让我成为了更好的自己。",
        "emotion": "calm",
        "keywords": ["六月", "总结", "成长", "感谢", "展望"]
    }
}

# Emotion to color mapping
EMOTION_COLORS = {
    "happy": "#ffd93d",
    "calm": "#8fb8ff",
    "anxious": "#ff6b6b",
    "sad": "#6bcf7f",
    "neutral": "#a8e6cf",
    "疲惫": "#c9b1ff",
    "怀念": "#ffb4e6"
}

# Chinese emotion labels
EMOTION_LABELS = {
    "happy": "开心",
    "calm": "平静",
    "anxious": "焦虑",
    "sad": "难过",
    "neutral": "中性",
    "疲惫": "疲惫",
    "怀念": "怀念"
}


class CoherentDiaryGenerator:
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

    def create_entry(self, content: str) -> dict:
        """Create an entry"""
        url = f"{self.base_url}/api/v1/entries"
        data = {
            "raw_content": content,
            "input_type": "text",
            "source_language": "zh-CN"
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

    def create_diary(self, entry_id: int, title: str, content: str, date_str: str) -> dict:
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
                # Diary already exists, try to get existing
                print(f"      ℹ️ Diary already exists for {date_str}")
                return self.get_diary_by_entry_id(entry_id)
            else:
                print(f"      ❌ Create diary failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"      ❌ Create diary error: {e}")
            return None

    def get_diary_by_entry_id(self, entry_id: int) -> dict:
        """Get diary by entry ID"""
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

    def create_memory_card(self, diary_id: int, emotion: str, keywords: List[str]) -> dict:
        """Create a memory card from diary"""
        url = f"{self.base_url}/api/v1/memories"
        emotion_label = EMOTION_LABELS.get(emotion, "平静")
        emotion_color = EMOTION_COLORS.get(emotion, "#8fb8ff")

        data = {
            "diary_id": diary_id,
            "emotion_label": emotion_label,
            "emotion_color": emotion_color,
            "keywords_json": json.dumps(keywords, ensure_ascii=False)
        }

        try:
            response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                return result["data"]
            elif response.status_code == 409:
                print(f"        ℹ️ Memory card already exists")
                return None
            else:
                print(f"        ❌ Create memory card failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"        ❌ Create memory card error: {e}")
            return None

    def get_existing_memories(self) -> dict:
        """Get existing memory cards as a set of diary dates"""
        url = f"{self.base_url}/api/v1/diaries"

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                diaries = result.get("data", [])
                # Return a set of diary dates
                return {d.get("diary_date") for d in diaries}
            return set()
        except Exception as e:
            print(f"  ❌ Get diaries error: {e}")
            return set()

    def generate_coherent_diaries(self):
        """Generate diary entries with coherent narratives"""
        print(f"\n📝 Generating coherent diaries for June 2026...")
        print(f"📖 This creates a time-series narrative with:")
        print(f"   - Work project progression (AI客服系统)")
        print(f"   - Personal relationship development (林月)")
        print(f"   - Health journey (健身)")
        print(f"   - Family events (爸爸生日, 妈妈老年大学)")
        print(f"   - Career growth (论文, 技术峰会)")
        print()

        # Get existing diaries to avoid duplicates
        existing_dates = self.get_existing_memories()
        print(f"  ℹ️ Existing diary dates: {len(existing_dates)}")
        print()

        success_count = 0
        skip_count = 0
        error_count = 0

        # Sort dates for chronological order
        dates = sorted(COHERENT_DIARIES.keys())

        for idx, date_str in enumerate(dates):
            diary_data = COHERENT_DIARIES[date_str]
            title = diary_data["title"]
            content = diary_data["content"]
            emotion = diary_data.get("emotion", "neutral")
            keywords = diary_data.get("keywords", [])

            print(f"  [{idx + 1}/{len(dates)}] {date_str} - {title}")

            # Skip if already exists
            if date_str in existing_dates:
                print(f"    ⏭️  Already exists, skipping")
                skip_count += 1
                continue

            # Step 1: Create entry
            entry_data = self.create_entry(content)
            if not entry_data:
                print(f"    ❌ Failed to create entry")
                error_count += 1
                continue

            entry_id = entry_data.get("id")
            print(f"    ✅ Entry created: ID {entry_id}")

            # Step 2: Create diary
            diary_result = self.create_diary(entry_id, title, content, date_str)
            if not diary_result:
                print(f"    ❌ Failed to create diary")
                error_count += 1
                continue

            diary_id = diary_result.get("id")
            print(f"    ✅ Diary created: ID {diary_id}")

            # Step 3: Create memory card
            memory_data = self.create_memory_card(diary_id, emotion, keywords)
            if memory_data:
                memory_id = memory_data.get("id")
                print(f"    ✅ Memory card created: ID {memory_id}")
                success_count += 1
            else:
                # Memory card might already exist, still count as success
                print(f"    ℹ️  Memory card already exists or skipped")
                success_count += 1

            print()

        print(f"📊 Summary:")
        print(f"  ✅ Successfully created: {success_count} diaries with memory cards")
        print(f"  ⏭️  Skipped (existing): {skip_count}")
        print(f"  ❌ Errors: {error_count}")
        print(f"  📝 Total dates: {len(dates)}")

    def run(self):
        """Execute the full coherent diary generation"""
        print("=" * 60)
        print("Inner Garden Coherent Diary Generator")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"User: {TEST_USER['username']} ({TEST_USER['email']})")
        print("-" * 60)

        # Step 1: Login
        if not self.login_user():
            print("❌ Failed to authenticate user")
            return False

        # Step 2: Generate coherent diaries
        self.generate_coherent_diaries()

        print("=" * 60)
        print("✅ Coherent diary generation completed!")
        print("=" * 60)
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate coherent diaries for time-series RAG testing")
    parser.add_argument("--local", action="store_true", help="Use local server (localhost:8000)")
    parser.add_argument("--url", type=str, help="Custom base URL")

    args = parser.parse_args()

    if args.url:
        base_url = args.url
    elif args.local:
        base_url = LOCAL_BASE_URL
    else:
        base_url = VPS_BASE_URL

    generator = CoherentDiaryGenerator(base_url)
    success = generator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
