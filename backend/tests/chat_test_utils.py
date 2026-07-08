"""
Test utilities for chat module testing.

Provides fake AI providers that avoid real OpenAI calls during testing.
"""
from __future__ import annotations

from typing import Literal

from app.services.ai_provider import AIProvider, AIResponse, AITimeoutError, AIProviderError, AIRateLimitError


class FakeAIProvider(AIProvider):
    """Fake AI provider for testing that returns predefined responses.

    Does NOT call OpenAI API.
    """

    def __init__(self, **kwargs):
        """Initialize fake provider with minimal config.

        Note: We skip parent __init__ to avoid OpenAI client creation.
        """
        self.provider = "fake"
        self.default_model = "fake-model"
        self.timeout = 30
        self.api_key = "fake-key"
        self.response_content = "这是 AI 的模拟回复内容。"
        self.call_count = 0

    def generate_response(
        self,
        messages: list[dict],
        context: str = "",
        mode: Literal["companion", "past_self"] = "companion",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AIResponse:
        """Generate fake AI response without calling OpenAI."""
        self.call_count += 1

        # Customize response based on mode
        if mode == "past_self":
            content = f"我是过去的你。{self.response_content}"
        else:
            content = f"作为你的陪伴者，{self.response_content}"

        return AIResponse(
            content=content,
            model_name=self.default_model,
            latency_ms=100,
            token_usage_input=50,
            token_usage_output=20,
        )

    def set_response(self, content: str):
        """Set custom response content for testing."""
        self.response_content = content


class TimeoutAIProvider(AIProvider):
    """Fake AI provider that simulates timeout.

    Always raises AITimeoutError.
    """

    def __init__(self, **kwargs):
        """Initialize timeout provider."""
        self.provider = "fake-timeout"
        self.default_model = "fake-model"
        self.timeout = 30
        self.api_key = "fake-key"

    def generate_response(
        self,
        messages: list[dict],
        context: str = "",
        mode: Literal["companion", "past_self"] = "companion",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AIResponse:
        """Always raise timeout error."""
        raise AITimeoutError("Simulated AI timeout")


class FailedAIProvider(AIProvider):
    """Fake AI provider that simulates provider error.

    Always raises AIProviderError.
    """

    def __init__(self, **kwargs):
        """Initialize failed provider."""
        self.provider = "fake-failed"
        self.default_model = "fake-model"
        self.timeout = 30
        self.api_key = "fake-key"
        self.error_message = "Simulated provider error"

    def generate_response(
        self,
        messages: list[dict],
        context: str = "",
        mode: Literal["companion", "past_self"] = "companion",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AIResponse:
        """Always raise provider error."""
        raise AIProviderError(self.error_message)

    def set_error_message(self, message: str):
        """Set custom error message for testing."""
        self.error_message = message


class RateLimitAIProvider(AIProvider):
    """Fake AI provider that simulates rate limiting.

    Always raises AIRateLimitError.
    """

    def __init__(self, **kwargs):
        """Initialize rate limit provider."""
        self.provider = "fake-ratelimit"
        self.default_model = "fake-model"
        self.timeout = 30
        self.api_key = "fake-key"

    def generate_response(
        self,
        messages: list[dict],
        context: str = "",
        mode: Literal["companion", "past_self"] = "companion",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AIResponse:
        """Always raise rate limit error."""
        raise AIRateLimitError("Simulated rate limit exceeded")


def setup_fake_provider():
    """Setup fake AI provider for testing.

    Monkey-patches the get_provider function to return FakeAIProvider.
    """
    from unittest.mock import patch

    fake_provider = FakeAIProvider()

    def mock_get_provider(**kwargs):
        return fake_provider

    return patch("app.services.chat_service.get_provider", side_effect=mock_get_provider)


def setup_timeout_provider():
    """Setup timeout AI provider for testing."""
    from unittest.mock import patch

    timeout_provider = TimeoutAIProvider()

    def mock_get_provider(**kwargs):
        return timeout_provider

    return patch("app.services.chat_service.get_provider", side_effect=mock_get_provider)


def setup_failed_provider():
    """Setup failed AI provider for testing."""
    from unittest.mock import patch

    failed_provider = FailedAIProvider()

    def mock_get_provider(**kwargs):
        return failed_provider

    return patch("app.services.chat_service.get_provider", side_effect=mock_get_provider)


def setup_ratelimit_provider():
    """Setup rate limit AI provider for testing."""
    from unittest.mock import patch

    ratelimit_provider = RateLimitAIProvider()

    def mock_get_provider(**kwargs):
        return ratelimit_provider

    return patch("app.services.chat_service.get_provider", side_effect=mock_get_provider)
