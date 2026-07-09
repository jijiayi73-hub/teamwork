"""Retrieval service for RAG-based chat feature.

This service searches for relevant diary entries to use as context
when generating AI responses.

Strategies:
- none: No retrieval (use_memory=False)
- keyword_emotion_time: Keyword + emotion + time-weighted search
- anchor_contextual: Anchor diary + related diaries in time window
- anchor_time_followup: Anchor + follow-up time range for continued conversation
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from ..models.diary import Diary, EmotionAnalysis
from ..utils.emotions import normalize_emotion_label


# ============================================================================
# Retrieval Result Types
# ============================================================================


class RetrievedDiary:
    """A diary entry with retrieval metadata."""

    def __init__(
        self,
        diary: Diary,
        relevance_score: float,
        source_type: Literal["anchor", "retrieved"],
    ):
        self.diary = diary
        self.relevance_score = relevance_score
        self.source_type = source_type

    def to_source_tuple(self) -> tuple[Diary, float, str]:
        """Convert to tuple for service layer processing."""
        return (self.diary, self.relevance_score, self.source_type)


# ============================================================================
# Retrieval Strategies
# ============================================================================


class RetrievalStrategy:
    """Base class for retrieval strategies."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def retrieve(self, query: str, **kwargs) -> list[RetrievedDiary]:
        """Execute retrieval strategy. Override in subclasses."""
        raise NotImplementedError

    def _filter_user_diaries(self) -> list[Diary]:
        """Get all non-deleted diaries for the user."""
        return (
            self.db.query(Diary)
            .filter(Diary.user_id == self.user_id, Diary.deleted_at.is_(None))
            .join(EmotionAnalysis)
            .all()
        )


class NoRetrievalStrategy(RetrievalStrategy):
    """No retrieval - use_memory=False."""

    def retrieve(self, query: str, **kwargs) -> list[RetrievedDiary]:
        return []


class KeywordEmotionTimeStrategy(RetrievalStrategy):
    """Keyword + emotion + time-weighted retrieval.

    Scores based on:
    1. Keyword matches in title/content (40%)
    2. Emotion similarity (30%)
    3. Time recency (30%)
    """

    def retrieve(self, query: str, **kwargs) -> list[RetrievedDiary]:
        diaries = self._filter_user_diaries()
        if not diaries:
            return []

        # Extract keywords from query (simple word splitting)
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        scored_results = []
        now = datetime.now().date()

        for diary in diaries:
            score = self._calculate_score(diary, keywords, now)
            if score > 0.3:  # Minimum relevance threshold
                scored_results.append(
                    RetrievedDiary(diary, score, "retrieved")
                )

        # Sort by relevance score descending
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_results[:5]  # Top 5 results

    def _extract_keywords(self, query: str) -> set[str]:
        """Extract keywords from query (Chinese and English words)."""
        # Simple Chinese word extraction (each character is a potential keyword)
        # For production, consider using jieba or similar tokenizer
        keywords = set()

        # Extract Chinese characters
        chinese_chars = re.findall(r'[一-鿿]+', query)
        for chars in chinese_chars:
            keywords.update(chars)

        # Extract English words
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        keywords.update(english_words)

        return keywords

    def _calculate_score(self, diary: Diary, keywords: set[str], now: date) -> float:
        """Calculate relevance score for a diary."""
        keyword_score = self._keyword_score(diary, keywords)
        emotion_score = self._emotion_score(diary, keywords)
        time_score = self._time_score(diary, now)

        return (keyword_score * 0.4 + emotion_score * 0.3 + time_score * 0.3)

    def _keyword_score(self, diary: Diary, keywords: set[str]) -> float:
        """Score based on keyword matches."""
        if not keywords:
            return 0.0

        text = (diary.title + " " + diary.content).lower()
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(matches / len(keywords), 1.0)

    def _emotion_score(self, diary: Diary, keywords: set[str]) -> float:
        """Score based on emotion relevance."""
        # Emotion-related keywords mapping
        emotion_keywords = {
            "焦虑": [
                "焦虑", "担心", "紧张", "不安", "压力",
                "anxiety", "anxious", "worry", "nervous", "stress", "stressed", "overwhelmed",
            ],
            "难过": ["难过", "伤心", "悲伤", "抑郁", "sad", "sadness", "depressed", "upset"],
            "anger": ["生气", "愤怒", "恼火", "angry", "mad", "furious"],
            "开心": ["开心", "快乐", "高兴", "joy", "happy", "excited"],
            "平静": ["平静", "放松", "轻松", "calm", "relaxed", "peaceful"],
        }

        query_emotions = set()
        for emotion, emotion_kw in emotion_keywords.items():
            if any(kw in " ".join(keywords) for kw in emotion_kw):
                query_emotions.add(emotion)

        if not query_emotions:
            return 0.5  # Neutral score if no emotion keywords

        if not diary.analysis:
            return 0.3  # No analysis data

        primary_emotion = normalize_emotion_label(diary.analysis.primary_emotion)
        if primary_emotion in query_emotions:
            return 1.0
        return 0.3

    def _time_score(self, diary: Diary, now: date) -> float:
        """Score based on time recency."""
        days_ago = (now - diary.diary_date).days
        if days_ago < 0:
            days_ago = 0

        # Decay function: recent diaries score higher
        # Score = 1.0 for today, 0.5 for 30 days ago, 0.1 for 90+ days
        if days_ago < 7:
            return 1.0
        elif days_ago < 30:
            return 0.7
        elif days_ago < 90:
            return 0.4
        else:
            return 0.1


class AnchorContextualStrategy(RetrievalStrategy):
    """Anchor diary + related diaries in time window."""

    def retrieve(self, query: str, **kwargs) -> list[RetrievedDiary]:
        anchor_diary_id = kwargs.get("anchor_diary_id")
        if not anchor_diary_id:
            return []

        # Get anchor diary
        anchor = (
            self.db.query(Diary)
            .filter(
                Diary.id == anchor_diary_id,
                Diary.user_id == self.user_id,
                Diary.deleted_at.is_(None),
            )
            .first()
        )

        if not anchor:
            return []

        results = [RetrievedDiary(anchor, 1.0, "anchor")]

        # Get related diaries in time window (±7 days)
        time_window = timedelta(days=7)
        start_date = anchor.diary_date - time_window
        end_date = anchor.diary_date + time_window

        related = (
            self.db.query(Diary)
            .filter(
                Diary.user_id == self.user_id,
                Diary.deleted_at.is_(None),
                Diary.id != anchor_diary_id,
                Diary.diary_date >= start_date,
                Diary.diary_date <= end_date,
            )
            .order_by(Diary.diary_date.desc())
            .limit(3)
            .all()
        )

        for diary in related:
            # Score based on proximity to anchor date
            days_diff = abs((diary.diary_date - anchor.diary_date).days)
            score = max(0.0, 1.0 - (days_diff / 14))  # Decay over 14 days
            results.append(RetrievedDiary(diary, score, "retrieved"))

        return results


class AnchorTimeFollowupStrategy(RetrievalStrategy):
    """Anchor + follow-up time range for continued conversation.

    This strategy is used for subsequent messages in a past_self conversation.
    It retrieves the anchor diary plus any diaries after the anchor date.
    """

    def retrieve(self, query: str, **kwargs) -> list[RetrievedDiary]:
        anchor_diary_id = kwargs.get("anchor_diary_id")
        if not anchor_diary_id:
            return []

        # Get anchor diary
        anchor = (
            self.db.query(Diary)
            .filter(
                Diary.id == anchor_diary_id,
                Diary.user_id == self.user_id,
                Diary.deleted_at.is_(None),
            )
            .first()
        )

        if not anchor:
            return []

        results = [RetrievedDiary(anchor, 1.0, "anchor")]

        # Get diaries after anchor date (up to 30 days)
        end_date = anchor.diary_date + timedelta(days=30)

        followup = (
            self.db.query(Diary)
            .filter(
                Diary.user_id == self.user_id,
                Diary.deleted_at.is_(None),
                Diary.id != anchor_diary_id,
                Diary.diary_date > anchor.diary_date,
                Diary.diary_date <= end_date,
            )
            .order_by(Diary.diary_date.asc())
            .limit(3)
            .all()
        )

        for diary in followup:
            results.append(RetrievedDiary(diary, 0.8, "retrieved"))

        return results


# ============================================================================
# Strategy Factory
# ============================================================================


STRATEGY_MAP: dict[
    str, type[RetrievalStrategy] | type[NoRetrievalStrategy]
] = {
    "none": NoRetrievalStrategy,
    "keyword_emotion_time": KeywordEmotionTimeStrategy,
    "anchor_contextual": AnchorContextualStrategy,
    "anchor_time_followup": AnchorTimeFollowupStrategy,
}


def get_strategy(
    strategy_name: str,
) -> type[RetrievalStrategy] | type[NoRetrievalStrategy]:
    """Get strategy class by name."""
    strategy = STRATEGY_MAP.get(strategy_name)
    if not strategy:
        return NoRetrievalStrategy
    return strategy


# ============================================================================
# Main Service Interface
# ============================================================================


def retrieve_context(
    db: Session,
    user_id: int,
    query: str,
    use_memory: bool,
    mode: Literal["companion", "past_self"] | None = None,
    anchor_diary_id: int | None = None,
    is_followup: bool = False,
) -> tuple[list[RetrievedDiary], str]:
    """Retrieve relevant diaries for chat context.

    Args:
        db: Database session
        user_id: Current user ID
        query: User's message/query
        use_memory: Whether to retrieve historical context
        mode: Conversation mode (companion or past_self)
        anchor_diary_id: Anchor diary ID for past_self mode
        is_followup: Whether this is a follow-up message in existing conversation

    Returns:
        Tuple of (list of RetrievedDiary, strategy_name)
    """
    # Determine strategy
    if not use_memory:
        strategy = NoRetrievalStrategy(db, user_id)
        strategy_name = "none"
    elif mode == "past_self" and anchor_diary_id:
        if is_followup:
            strategy = AnchorTimeFollowupStrategy(db, user_id)
            strategy_name = "anchor_time_followup"
        else:
            strategy = AnchorContextualStrategy(db, user_id)
            strategy_name = "anchor_contextual"
    else:
        strategy = KeywordEmotionTimeStrategy(db, user_id)
        strategy_name = "keyword_emotion_time"

    # Execute retrieval
    results = strategy.retrieve(query, anchor_diary_id=anchor_diary_id)

    return results, strategy_name
