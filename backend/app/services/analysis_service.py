import json


NEGATIVE_WORDS = ("难过", "焦虑", "累", "疲惫", "生气", "害怕", "压力", "失眠", "崩溃")
POSITIVE_WORDS = ("开心", "顺利", "平静", "喜欢", "期待", "放松", "谢谢", "满足")


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
