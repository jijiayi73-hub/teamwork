from __future__ import annotations

CANONICAL_EMOTIONS = ("开心", "平静", "焦虑", "难过", "疲惫", "怀念", "中性")

_EMOTION_ALIASES = {
    "joy": "开心",
    "happy": "开心",
    "happiness": "开心",
    "joyful": "开心",
    "grateful": "开心",
    "gratitude": "开心",
    "开心": "开心",
    "快乐": "开心",
    "喜悦": "开心",
    "愉快": "开心",
    "calm": "平静",
    "peace": "平静",
    "peaceful": "平静",
    "relieved": "平静",
    "relief": "平静",
    "平静": "平静",
    "安定": "平静",
    "安宁": "平静",
    "放松": "平静",
    "anxiety": "焦虑",
    "anxious": "焦虑",
    "worry": "焦虑",
    "worried": "焦虑",
    "fear": "焦虑",
    "stress": "焦虑",
    "stressed": "焦虑",
    "焦虑": "焦虑",
    "紧张": "焦虑",
    "担心": "焦虑",
    "担忧": "焦虑",
    "压力": "焦虑",
    "sad": "难过",
    "sadness": "难过",
    "melancholy": "难过",
    "down": "难过",
    "low": "难过",
    "难过": "难过",
    "伤心": "难过",
    "低落": "难过",
    "沮丧": "难过",
    "tired": "疲惫",
    "fatigue": "疲惫",
    "exhausted": "疲惫",
    "weary": "疲惫",
    "疲惫": "疲惫",
    "疲劳": "疲惫",
    "累": "疲惫",
    "nostalgia": "怀念",
    "nostalgic": "怀念",
    "missing": "怀念",
    "miss": "怀念",
    "怀念": "怀念",
    "想念": "怀念",
    "neutral": "中性",
    "unknown": "中性",
    "中性": "中性",
    "普通": "中性",
    "未知": "中性",
}


def normalize_emotion_label(value: str | None, default: str = "中性") -> str:
    """Return the Chinese canonical emotion label used by diary and memory APIs."""
    if not value:
        return default
    key = str(value).strip()
    if not key:
        return default
    return _EMOTION_ALIASES.get(key.lower(), _EMOTION_ALIASES.get(key, key if key in CANONICAL_EMOTIONS else default))
