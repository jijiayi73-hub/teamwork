"""Retrieval Trigger service for lightweight context retrieval decision.

This service replaces LLM-based retrieval decision with a fast, rule-based
approach. It uses simple pattern matching to determine when to retrieve
historical context, allowing Memory Gate to make the final decision.

The goal is to retrieve more proactively while keeping costs and latency low.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)


# ============================================================================
# Trigger Patterns
# ============================================================================

# Explicit memory references (strong trigger)
EXPLICIT_MEMORY_PATTERNS = [
    r"还记得.*吗",       # "还记得...吗"
    r"那.*事",           # "那件事"、"那天"
    r"之前.*过",         # "之前...过"
    r"以前.*过",         # "以前...过"
    r"上次.*",           # "上次..."
    r"过去.*",           # "过去..."
    r"那时候",           # "那时候"
    r"后来",             # "后来"
    r"之后",             # "之后"
    r"回.*想",           # "回想"、"回想一下"、"让我回想"
    r"回.*忆",           # "回忆"、"回忆一下"
    r"记.*得",           # "记...得"
    r"记.*不.*得",       # "记不记得"
    r"想.*起.*来",       # "想起来"、"我想起来了"
    r"想.*一.*想",       # "想一想"、"让我想一想"
    r"想.*想",           # "想想"
    r"想.*起",           # "想起"、"没想起"
    r"记得.*吗",         # "记得吗"
    r"还.*记.*得",       # "还记得"、"还记不记得"
    r"有.*没.*有",       # "有没有"、"有没有记得"
    r"那.*个",           # "那个"、"那个时候"
]

# Continuity expressions (strong trigger)
CONTINUITY_PATTERNS = [
    r"又",               # "又..."
    r"还是",             # "还是..."
    r"一直",             # "一直..."
    r"每次",             # "每次..."
    r"总是",             # "总是..."
    r"越来越",           # "越来越..."
    r"又来了",           # "又来了"
    r"还是老样子",       # "还是老样子"
    r"像以前一样",       # "像以前一样"
    r"接着",             # "接着..."
    r"继续",             # "继续..."
    r"还是那",           # "还是那..."
    r"又是",             # "又是..."
    r"总是那",           # "总是那..."
    r"还是.*那",         # "还是那样"
    r"再次",             # "再次..."
    r"又一次",           # "又一次..."
    r"还.*在",           # "还在..."
    r"依.*旧",           # "依旧..."
    r"照.*旧",           # "照旧..."
    r"照.*样",           # "照样..."
    r"如.*故",           # "如故..."
    r".*如故",           # "一切如故"、"如故"
]

# Emotion/theme references (medium trigger)
EMOTION_THEME_PATTERNS = [
    r"焦虑",             # 直接情绪词
    r"难过",
    r"开心",
    r"生气",
    r"担心",
    r"压力",
    r"累",               # "累了"、"好累"
    r"烦",
    r"郁闷",
    r"开心不起来",
]

# Question patterns (weak trigger - might benefit from context)
QUESTION_PATTERNS = [
    r"怎么办",           # 寻求建议
    r"怎么",             # 一般疑问
    r"为什么",           # 原因询问
    r"是不是",           # 确认询问
    r"如何",             # 方法询问
    r".*\?",             # 英文问号
]

# Negative patterns (suppress retrieval)
NEGATIVE_PATTERNS = [
    r"^你好",            # 纯问候
    r"^嗨",
    r"^在吗",
    r"^在不在",
    r"^test",            # 测试消息
]


# ============================================================================
# Trigger Result
# ============================================================================


@dataclass
class RetrievalTriggerResult:
    """Result of retrieval trigger decision."""

    should_retrieve: bool
    trigger_reason: str
    confidence: float  # 0.0 to 1.0
    trigger_type: Literal["explicit", "continuity", "emotion", "question", "default"]


# ============================================================================
# Retrieval Trigger Service
# ============================================================================


class RetrievalTriggerService:
    """Service for fast retrieval triggering.

    This service uses rule-based pattern matching to decide whether to
    retrieve historical context. It's much faster and cheaper than LLM-based
    decision while still being effective.

    Strategy:
    1. Check negative patterns (skip retrieval)
    2. Check explicit memory references (strong trigger)
    3. Check continuity expressions (strong trigger)
    4. Check emotion/theme references (medium trigger)
    5. Check question patterns (weak trigger)
    6. Default: retrieve conservatively
    """

    def __init__(
        self,
        default_retrieve: bool = True,  # Default behavior when no patterns match
        question_threshold: float = 0.3,  # Threshold for question-triggered retrieval
    ):
        """Initialize retrieval trigger service.

        Args:
            default_retrieve: Whether to retrieve by default when no patterns match
            question_threshold: Minimum confidence for question-triggered retrieval
        """
        self.default_retrieve = default_retrieve
        self.question_threshold = question_threshold

        # Compile regex patterns for efficiency
        self.explicit_patterns = [re.compile(p, re.IGNORECASE) for p in EXPLICIT_MEMORY_PATTERNS]
        self.continuity_patterns = [re.compile(p, re.IGNORECASE) for p in CONTINUITY_PATTERNS]
        self.emotion_patterns = [re.compile(p, re.IGNORECASE) for p in EMOTION_THEME_PATTERNS]
        self.question_patterns = [re.compile(p, re.IGNORECASE) for p in QUESTION_PATTERNS]
        self.negative_patterns = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_PATTERNS]

    def should_retrieve(
        self,
        user_message: str,
        mode: Literal["companion", "past_self"] = "companion",
    ) -> RetrievalTriggerResult:
        """Decide whether to retrieve historical context.

        Args:
            user_message: User's message
            mode: Conversation mode (past_self always retrieves)

        Returns:
            RetrievalTriggerResult with decision and metadata
        """
        # Past_self mode always retrieves
        if mode == "past_self":
            return RetrievalTriggerResult(
                should_retrieve=True,
                trigger_reason="past_self_mode_always_retrieves",
                confidence=1.0,
                trigger_type="explicit",
            )

        # Skip empty messages
        if not user_message or len(user_message.strip()) < 2:
            return RetrievalTriggerResult(
                should_retrieve=False,
                trigger_reason="message_too_short",
                confidence=0.0,
                trigger_type="default",
            )

        message = user_message.strip()

        # Check negative patterns (skip retrieval)
        for pattern in self.negative_patterns:
            if pattern.match(message):
                return RetrievalTriggerResult(
                    should_retrieve=False,
                    trigger_reason="greeting_or_test_message",
                    confidence=0.0,
                    trigger_type="default",
                )

        # Check explicit memory references (strong trigger)
        for pattern in self.explicit_patterns:
            if pattern.search(message):
                return RetrievalTriggerResult(
                    should_retrieve=True,
                    trigger_reason="explicit_memory_reference",
                    confidence=0.9,
                    trigger_type="explicit",
                )

        # Check continuity expressions (strong trigger)
        for pattern in self.continuity_patterns:
            if pattern.search(message):
                return RetrievalTriggerResult(
                    should_retrieve=True,
                    trigger_reason="continuity_expression",
                    confidence=0.85,
                    trigger_type="continuity",
                )

        # Check emotion/theme references (medium trigger)
        for pattern in self.emotion_patterns:
            if pattern.search(message):
                return RetrievalTriggerResult(
                    should_retrieve=True,
                    trigger_reason="emotion_or_theme_reference",
                    confidence=0.7,
                    trigger_type="emotion",
                )

        # Check question patterns (weak trigger)
        for pattern in self.question_patterns:
            if pattern.search(message):
                return RetrievalTriggerResult(
                    should_retrieve=self.default_retrieve,  # Use default
                    trigger_reason="question_potential_context",
                    confidence=self.question_threshold,
                    trigger_type="question",
                )

        # Default: use configured default behavior
        # For companion mode, we default to retrieving to provide better context
        # Memory Gate will make the final decision on whether to use the context
        return RetrievalTriggerResult(
            should_retrieve=self.default_retrieve,
            trigger_reason="default_proactive_retrieval",
            confidence=0.4 if self.default_retrieve else 0.0,
            trigger_type="default",
        )


# ============================================================================
# Singleton Instance
# ============================================================================

_default_trigger: RetrievalTriggerService | None = None


def get_retrieval_trigger() -> RetrievalTriggerService:
    """Get the default retrieval trigger service instance.

    Reads configuration from settings to control trigger behavior.

    Returns:
        RetrievalTriggerService singleton
    """
    global _default_trigger
    if _default_trigger is None:
        # Read from configuration
        try:
            from ..config import settings
            default_retrieve = getattr(settings, "rag_retrieve_by_default", True)
            question_threshold = getattr(settings, "rag_question_trigger_threshold", 0.3)

            logger.info(
                f"Initializing RetrievalTrigger: default_retrieve={default_retrieve}, "
                f"question_threshold={question_threshold}"
            )

            _default_trigger = RetrievalTriggerService(
                default_retrieve=default_retrieve,
                question_threshold=question_threshold,
            )
        except Exception as e:
            logger.warning(f"Failed to read settings, using defaults: {e}")
            _default_trigger = RetrievalTriggerService(default_retrieve=True)
    return _default_trigger
