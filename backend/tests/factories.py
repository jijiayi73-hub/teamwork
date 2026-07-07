"""
Test data factories for InnerGarden API tests.
"""

from datetime import date, datetime, timezone


def user_data(
    username: str = "testuser",
    email: str = "testuser@example.com",
    password: str = "testpass123",
    role: str = "user"
) -> dict:
    """Generate user registration data."""
    return {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }


def login_data(email: str = "testuser@example.com", password: str = "testpass123") -> dict:
    """Generate user login data."""
    return {
        "email": email,
        "password": password
    }


def entry_data(
    raw_content: str = "今天天气真好，心情很愉快！",
    input_type: str = "text",
    source_language: str = "zh-CN"
) -> dict:
    """Generate entry creation data."""
    return {
        "raw_content": raw_content,
        "input_type": input_type,
        "source_language": source_language
    }


def diary_data(
    entry_id: int = 1,
    title: str = "测试日记",
    content: str = "这是一篇测试日记的内容",
    diary_date: str = None,
    is_favorite: bool = False
) -> dict:
    """Generate diary creation data."""
    if diary_date is None:
        diary_date = date.today().isoformat()
    return {
        "entry_id": entry_id,
        "title": title,
        "content": content,
        "diary_date": diary_date,
        "is_favorite": is_favorite
    }


def diary_update_data(
    title: str = None,
    content: str = None,
    diary_date: str = None,
    is_favorite: bool = None
) -> dict:
    """Generate diary update data."""
    data = {}
    if title is not None:
        data["title"] = title
    if content is not None:
        data["content"] = content
    if diary_date is not None:
        data["diary_date"] = diary_date
    if is_favorite is not None:
        data["is_favorite"] = is_favorite
    return data


def analysis_data(
    primary_emotion: str = "joy",
    emotion_score: int = 75,
    valence: float = 0.5,
    arousal: float = 0.5,
    intensity: float = 0.6,
    risk_level: str = "low",
    summary: str = "这是一段积极的内容",
    suggestion: str = "保持这种好心情！"
) -> dict:
    """Generate emotion analysis data."""
    return {
        "primary_emotion": primary_emotion,
        "secondary_emotions": [],
        "emotion_score": emotion_score,
        "valence": valence,
        "arousal": arousal,
        "intensity": intensity,
        "risk_level": risk_level,
        "risk_reason": None,
        "summary": summary,
        "suggestion": suggestion
    }


# Test content samples for different emotions
POSITIVE_CONTENT = "今天太开心了，收到了一份惊喜礼物！"
NEGATIVE_CONTENT = "工作压力很大，感觉快要崩溃了。"
NEUTRAL_CONTENT = "今天是一个普通的日子，没有什么特别的事情发生。"
ANXIETY_CONTENT = "明天要考试了，心里很焦虑，担心考不好。"
CALM_CONTENT = "坐在公园里，看着湖面，内心感到平静。"
