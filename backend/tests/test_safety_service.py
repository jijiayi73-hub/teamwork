from __future__ import annotations

from app.services.safety_service import SafetyService, get_safety_service, reset_safety_service


def test_safe_content_is_not_flagged():
    result = SafetyService().check_content_safety("I had a calm walk today.")
    assert result.flagged is False
    assert result.level == "none"
    assert result.category is None
    assert result.action == "none"


def test_self_harm_has_high_priority():
    result = SafetyService().check_content_safety("I want to die and hurt others")
    assert result.flagged is True
    assert result.level == "high"
    assert result.category == "self_harm_risk"
    assert result.action == "suggest_support"


def test_violence_and_distress_are_flagged():
    violence = SafetyService().check_content_safety("I want to kill someone")
    assert violence.flagged is True
    assert violence.category == "violence_risk"
    assert violence.level == "medium"

    distress = SafetyService().check_content_safety("I feel hopeless")
    assert distress.flagged is True
    assert distress.category == "emotional_distress"
    assert distress.action == "suggest_support"


def test_ai_response_uses_same_safety_logic():
    result = SafetyService().check_ai_response("This sounds hopeless")
    assert result.flagged is True
    assert result.category == "emotional_distress"


def test_safety_service_singleton_can_reset():
    reset_safety_service()
    first = get_safety_service()
    second = get_safety_service()
    assert first is second
    reset_safety_service()
    assert get_safety_service() is not first
