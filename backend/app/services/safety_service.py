"""Content safety check service for RAG chat feature.

This service provides content safety checking to detect potentially
concerning content in user messages and AI responses.

For v1, this is a simple keyword-based implementation.
Future versions can integrate with professional safety APIs.
"""
from __future__ import annotations

import re
from typing import Literal


# ============================================================================
# Safety Check Data
# ============================================================================


class SafetyCheck:
    """Content safety check result with structured enums."""

    def __init__(
        self,
        flagged: bool,
        level: Literal["none", "low", "medium", "high"],
        category: Literal["emotional_distress", "self_harm_risk", "violence_risk"] | None,
        action: Literal["none", "show_notice", "suggest_support", "trigger_emergency_flow"],
    ):
        self.flagged = flagged
        self.level = level
        self.category = category
        self.action = action

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "flagged": self.flagged,
            "level": self.level,
            "category": self.category,
            "action": self.action,
        }


# ============================================================================
# Safety Keywords (Chinese and English)
# ============================================================================

# Self-harm related keywords
SELF_HARM_KEYWORDS = [
    # Chinese
    "自杀", "想死", "不想活了", "结束生命", "了断", "割腕", "跳楼",
    "上吊", "服毒", "自杀", "轻生", "伤害自己", "自残", "割手",
    # English
    "suicide", "kill myself", "want to die", "end it all", "cut myself",
    "self harm", "hurt myself", "slash wrist", "jump off", "hang myself",
]

# Violence keywords (harm to others)
VIOLENCE_KEYWORDS = [
    # Chinese
    "杀人", "杀了", "想杀人", "伤害别人", "报复", "弄死", "弄死他",
    # English
    "kill someone", "want to kill", "murder", "hurt others", "revenge",
]

# Severe emotional distress keywords
DISTRESS_KEYWORDS = [
    # Chinese
    "崩溃", "绝望", "撑不下去", "无法承受", "痛苦", "受不了", "想放弃",
    "没有希望", "绝望", "崩溃", "撑不住了", "活不下去",
    # English
    "breakdown", "hopeless", "can't go on", "unbearable", "suffering",
    "can't take it", "want to give up", "despair", "falling apart",
]


# ============================================================================
# Safety Check Service
# ============================================================================


class SafetyService:
    """Content safety check service."""

    def __init__(self):
        """Initialize safety service with default keyword lists."""
        self.self_harm_keywords = set(SELF_HARM_KEYWORDS)
        self.violence_keywords = set(VIOLENCE_KEYWORDS)
        self.distress_keywords = set(DISTRESS_KEYWORDS)

    def check_content_safety(self, content: str) -> SafetyCheck:
        """Check content for safety concerns.

        Args:
            content: Text content to check

        Returns:
            SafetyCheck with structured result
        """
        content_lower = content.lower()

        # Check for self-harm risk (highest priority)
        self_harm_matches = self._check_keywords(
            content_lower, self.self_harm_keywords
        )
        if self_harm_matches:
            return SafetyCheck(
                flagged=True,
                level="high",
                category="self_harm_risk",
                action="suggest_support",
            )

        # Check for violence risk
        violence_matches = self._check_keywords(
            content_lower, self.violence_keywords
        )
        if violence_matches:
            return SafetyCheck(
                flagged=True,
                level="medium",
                category="violence_risk",
                action="show_notice",
            )

        # Check for emotional distress
        distress_matches = self._check_keywords(
            content_lower, self.distress_keywords
        )
        if distress_matches:
            # Determine level based on intensity
            if "绝望" in content_lower or "hopeless" in content_lower:
                level = "medium"
                action = "suggest_support"
            else:
                level = "low"
                action = "show_notice"

            return SafetyCheck(
                flagged=True,
                level=level,
                category="emotional_distress",
                action=action,
            )

        # No concerns detected
        return SafetyCheck(
            flagged=False,
            level="none",
            category=None,
            action="none",
        )

    def _check_keywords(self, content: str, keywords: set[str]) -> bool:
        """Check if any keyword is present in content.

        Args:
            content: Content to check (lowercase)
            keywords: Set of keywords to check for

        Returns:
            True if any keyword found
        """
        for keyword in keywords:
            if keyword.lower() in content:
                return True
        return False

    def check_ai_response(self, content: str) -> SafetyCheck:
        """Check AI response for safety concerns.

        For now, this uses the same logic as user content.
        In future, we might want to check if AI is giving inappropriate advice.

        Args:
            content: AI generated content

        Returns:
            SafetyCheck with structured result
        """
        # For v1, same logic applies
        # Future: check if AI gives medical/legal advice, etc.
        return self.check_content_safety(content)


# ============================================================================
# Singleton Instance
# ============================================================================


_service: SafetyService | None = None


def get_safety_service() -> SafetyService:
    """Get or create safety service instance.

    Returns:
        SafetyService instance
    """
    global _service

    if _service is None:
        _service = SafetyService()

    return _service


def reset_safety_service() -> None:
    """Reset global service instance (useful for testing)."""
    global _service
    _service = None
