import json
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


NEGATIVE_WORDS = ("难过", "焦虑", "累", "疲惫", "生气", "害怕", "压力", "失眠", "崩溃")
POSITIVE_WORDS = ("开心", "顺利", "平静", "喜欢", "期待", "放松", "谢谢", "满足")


# Emotion analysis LLM prompt
EMOTION_ANALYSIS_SYSTEM_PROMPT = """你是一个温柔、善解人意的情绪分析专家。你的任务是分析用户文本中的情绪状态。

请仔细阅读用户的文字，理解其中的情绪色彩，包括：
1. 主要情绪 - 最强烈的情绪（joy/sadness/anxiety/calm/neutral）
2. 次要情绪 - 伴随的其他情绪（可选）
3. 情绪分数 - 20-85 之间，越积极越高
4. 效价 -0.5 到 0.5，负数表示消极，正数表示积极
5. 唤醒度 0.0 到 1.0，情绪的强烈程度
6. 强度 0.0 到 1.0，整体情绪强度
7. 风险等级 low/medium/high - 是否需要额外关注
8. 风险原因 - 如果风险等级不是 low，简要说明原因
9. 总结 - 一句简短温暖的话，概括用户的情绪状态
10. 建议 - 一句温柔的建议，不带说教

返回 JSON 格式（必须严格遵循，不要添加任何其他文字）：
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
  "suggestion": "温暖建议"
}

注意：
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

            # 生成 diary_content（如果 LLM 没有提供）
            if "diary_content" not in result:
                result["diary_content"] = f"今天我记录下了这段感受：{raw_content}"

        except (json.JSONDecodeError, ValueError) as e:
            # JSON 解析失败，回退到规则分析
            return analyze_text(raw_content)

        # 添加 raw_response_json
        result["raw_response_json"] = json.dumps(result, ensure_ascii=False)

        return result

    except Exception as e:
        # LLM 调用失败，回退到规则分析
        return analyze_text(raw_content)


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
    """根据情绪生成标题。"""
    titles = {
        "joy": "开心的时刻",
        "sadness": "低落的时刻",
        "anxiety": "焦虑的时刻",
        "calm": "平静的时刻",
        "neutral": "今天的记录",
    }
    return titles.get(emotion, "今天的心情记录")
