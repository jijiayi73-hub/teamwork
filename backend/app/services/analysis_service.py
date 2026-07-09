import json
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


NEGATIVE_WORDS = ("难过", "焦虑", "累", "疲惫", "生气", "害怕", "压力", "失眠", "崩溃")
POSITIVE_WORDS = ("开心", "顺利", "平静", "喜欢", "期待", "放松", "谢谢", "满足")


# Emotion analysis LLM prompt
EMOTION_ANALYSIS_SYSTEM_PROMPT = """你是 Inner Garden 的对话结构化分析模块。

你不会直接与用户交流。你的任务是根据当前用户消息、最近对话和系统提供的历史记录，提取用于情绪日记、数据库存储和趋势分析的信息。

# 基本原则

1. 只根据用户明确表达的内容进行分析
2. 不进行心理疾病诊断
3. 不推断稳定人格
4. 不把模型猜测当作事实
5. 不虚构事件、人物、时间和原因
6. 信息不足时使用克制表达
7. 多种情绪可以同时存在

# 返回 JSON 格式

请严格返回以下 JSON 格式（不要添加任何其他文字）：
{
  "primary_emotion": "joy|sadness|anxiety|calm|neutral",
  "secondary_emotions": ["emotion1", "emotion2"],
  "emotion_score": 20-85,
  "valence": -0.5 到 0.5,
  "arousal": 0.0 到 1.0,
  "intensity": 0.0 到 1.0,
  "risk_level": "low|medium|high",
  "risk_reason": "原因描述",
  "summary": "简短总结",
  "suggestion": "温暖建议",
  "title": "日记标题（4-12字，文艺诗意，含蓄不直白）",
  "diary_content": "结构化的日记叙述文（150-400字）"
}

# title 生成规则

生成文艺、诗意、含蓄的标题，避免直白描述情绪：
- 不用"开心的日子"、"焦虑的时刻"等直白表达
- 使用意象和隐喻，如"微光"、"港湾"、"涟漪"等
- 保持简洁（4-12字）
- 可以借用自然意象（阳光、雨、风、云）或空间意象（港湾、角落、窗户）
- 参考示例：
  - 开心时："微光点亮的日子"、"云开见月"
  - 平静时："内心的宁静港湾"、"湖面如镜"
  - 低落时："雨后才有彩虹"、"夜色终会过去"
  - 焦虑时："翻涌过后是平静"、"风暴前的宁静"
  - 中性时："平凡中的诗意"、"亦言亦思皆为序章"
# diary_content 生成规则

当用户消息和对话内容足够时，生成一篇结构化的日记叙述文：

1. 使用第一人称，保持用户自己的语气和口吻
2. **严格忠于用户原意，不虚构任何事件、人物、时间、原因**
3. **只写入用户明确表达的内容，不添加推断或猜测**
4. 将用户的多句话语整理成连贯的叙述，而非简单对话拼接
5. 保持自然和真实感，不加入用户没有表达的结论或评判
6. 可以适当加入过渡语句使内容流畅，但不能添加新的信息

日记应包含以下结构：
- 开头：日期或时间背景（如"今天"、"这一天"）
- 中间：用户表达的**具体内容**（用户说了什么、经历了什么、感受如何）
- 结尾：用户表达的**期望或想法**（如果用户有表达，否则写一句温和的自我回应）

示例格式：
```
x月x日

示例格式：
```
x月x日

今天[用户表达的日期背景]。[用户说的具体事件和想法，用自己的话整理]。

[用户表达的感受和在意的地方]。

[用户表达的期待或想法，如果没有，写：希望明天也能继续向前。]
```

重要提醒：
- 不要编造用户没有说的事件或感受
- 不要加入诊断或评判性结论
- 如果用户只表达了感受，就只写感受，不要添加事件
- 如果信息不足，diary_content 返回空字符串 ""

# 注意事项

- 你不是医疗专业人士，不要给出诊断
- 如果用户表达自残想法，risk_level 设为 high
- 保持语调温暖、理解、不评判"""


def analyze_text(raw_content: str) -> dict:
    negative_hits = sum(word in raw_content for word in NEGATIVE_WORDS)
    positive_hits = sum(word in raw_content for word in POSITIVE_WORDS)
    if negative_hits > positive_hits:
        primary_emotion = "anxiety" if "焦虑" in raw_content or "压力" in raw_content else "sadness"
        score = max(20, 50 - negative_hits * 10)
        valence = -0.4
    elif positive_hits > negative_hits:
        primary_emotion = "joy" if "开心" in raw_content else "calm"
        score = min(85, 55 + positive_hits * 10)
        valence = 0.5
    else:
        primary_emotion = "neutral"
        score = 50
        valence = 0.0

    risk_level = "medium" if any(word in raw_content for word in ("崩溃", "撑不住")) else "low"
    title = "今天的心情记录"
    diary_content = f"今天我记录下了这段感受：{raw_content}"
    summary = "这是一段关于今日事件和情绪的整理，适合保存后回看。"
    suggestion = "先把感受写下来已经很好了，可以给自己一点休息和缓冲。"
    result = {
        "title": title,
        "diary_content": diary_content,
        "primary_emotion": primary_emotion,
        "secondary_emotions": [],
        "emotion_score": score,
        "valence": valence,
        "arousal": 0.5 if negative_hits else 0.3,
        "intensity": min(1.0, 0.35 + 0.15 * (positive_hits + negative_hits)),
        "risk_level": risk_level,
        "risk_reason": "出现明显高压表达" if risk_level == "medium" else "未发现明显紧急风险表达",
        "summary": summary,
        "suggestion": suggestion,
    }
    result["raw_response_json"] = json.dumps(result, ensure_ascii=False)
    return result


def analyze_text_with_llm(
    raw_content: str,
    conversation_messages: list[dict] | None = None,
    db: Session | None = None,
) -> dict:
    """使用 LLM 进行情绪分析，支持对话上下文。

    Args:
        raw_content: 要分析的文本内容
        conversation_messages: 可选的对话上下文 [{role, content}, ...]
        db: 数据库会话（用于验证 conversation_id）

    Returns:
        与 analyze_text() 相同格式的 dict
    """
    # 提取纯用户内容（排除 AI 回复），用于 fallback
    user_only_content = _extract_user_content_from_conversation(conversation_messages, raw_content)

    try:
        from .ai_provider import get_provider
        from ..config import settings

        # 获取 AI Provider
        provider = get_provider(
            provider=settings.ai_provider,
            default_model=settings.ai_default_model,
            base_url=settings.deepseek_base_url if settings.ai_provider == "deepseek" else None,
            timeout=settings.ai_timeout,
        )

        # 构建用户消息
        user_content = raw_content

        # 如果有对话上下文，添加到消息中
        if conversation_messages and len(conversation_messages) > 0:
            context_parts = ["以下是这段文字的对话上下文，帮助理解用户的情绪状态："]
            for msg in conversation_messages[-5:]:  # 只取最近 5 条消息
                role_name = "用户" if msg.get("role") == "user" else "AI"
                context_parts.append(f"{role_name}：{msg.get('content', '')}")
            context_parts.append("\n现在需要分析的是用户最后表达的内容：")
            context_parts.append(raw_content)
            user_content = "\n".join(context_parts)

        # 调用 LLM
        messages = [
            {"role": "system", "content": EMOTION_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        response = provider.client.chat.completions.create(
            model=provider.default_model,
            messages=messages,
            temperature=0.3,  # 使用较低温度以获得更一致的输出
            max_tokens=500,
            timeout=provider.timeout,
        )

        # 解析响应
        content = response.choices[0].message.content or ""

        # 尝试解析 JSON
        try:
            # 移除可能的 markdown 代码块标记
            if content.strip().startswith("```"):
                lines = content.strip().split("\n")
                if lines[0].startswith("```json"):
                    content = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
                elif lines[0].startswith("```"):
                    content = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])

            result = json.loads(content)

            # 验证必需字段
            required_fields = [
                "primary_emotion", "secondary_emotions", "emotion_score",
                "valence", "arousal", "intensity", "risk_level",
                "risk_reason", "summary", "suggestion"
            ]

            for field in required_fields:
                if field not in result:
                    result[field] = _get_default_value(field)

            # 确保类型正确
            result["secondary_emotions"] = result.get("secondary_emotions", [])
            if not isinstance(result["secondary_emotions"], list):
                result["secondary_emotions"] = []

            # 生成 title（如果 LLM 没有提供）
            if "title" not in result:
                result["title"] = _generate_title_from_emotion(result["primary_emotion"])

            # 生成 diary_content（如果 LLM 没有提供或为空）
            if "diary_content" not in result or not result.get("diary_content", "").strip():
                # 使用纯用户内容作为 fallback，不包含 AI 回复
                result["diary_content"] = f"今天我记录下了这段感受：{user_only_content}"

        except (json.JSONDecodeError, ValueError) as e:
            # JSON 解析失败，回退到规则分析
            return analyze_text(user_only_content)

        # 添加 raw_response_json
        result["raw_response_json"] = json.dumps(result, ensure_ascii=False)

        return result

    except Exception as e:
        # LLM 调用失败，回退到规则分析
        return analyze_text(user_only_content)


def _get_default_value(field: str) -> any:
    """获取字段的默认值。"""
    defaults = {
        "primary_emotion": "neutral",
        "secondary_emotions": [],
        "emotion_score": 50,
        "valence": 0.0,
        "arousal": 0.3,
        "intensity": 0.5,
        "risk_level": "low",
        "risk_reason": "",
        "summary": "这是一段情绪的记录。",
        "suggestion": "记录下来已经很好了。",
        "title": "今天的心情记录",
        "diary_content": "",
    }
    return defaults.get(field, None)


def _generate_title_from_emotion(emotion: str) -> str:
    """根据情绪生成文艺风格的标题。"""
    titles = {
        "joy": "微光点亮的日子",
        "sadness": "雨后才有彩虹",
        "anxiety": "翻涌过后是平静",
        "calm": "内心的宁静港湾",
        "neutral": "平凡中的诗意",
    }
    return titles.get(emotion, "亦言亦思皆为序章")


def _extract_user_content_from_conversation(conversation_messages: list[dict] | None, raw_content: str) -> str:
    """从对话消息中提取用户内容，用于 fallback。

    优先使用 conversation_messages 中的用户消息（排除 AI 回复）。
    如果没有 conversation_messages 或提取失败，回退到 raw_content。

    Args:
        conversation_messages: 对话消息列表 [{role, content}, ...]
        raw_content: 原始内容（作为最后的 fallback）

    Returns:
        纯用户对话内容，用换行符连接
    """
    if conversation_messages and len(conversation_messages) > 0:
        # 提取用户消息（排除 AI 回复）
        user_messages = [
            msg.get("content", "") for msg in conversation_messages if msg.get("role") == "user"
        ]
        user_content = "\n".join(filter(bool, user_messages))
        if user_content.strip():
            return user_content
    # 回退到 raw_content
    return raw_content
