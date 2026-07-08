"""AI provider service for LLM integration.

This service handles all interactions with AI providers (currently OpenAI).
It provides a unified interface for generating chat responses with proper
error handling and metrics collection.
"""
from __future__ import annotations

import os
import time
from typing import Literal


# ============================================================================
# Custom Exceptions
# ============================================================================


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AITimeoutError(AIServiceError):
    """Raised when AI request times out."""
    pass


class AIProviderError(AIServiceError):
    """Raised when AI provider returns an error."""
    pass


class AIRateLimitError(AIServiceError):
    """Raised when rate limit is exceeded."""
    pass


class AIConfigError(AIServiceError):
    """Raised when configuration is invalid."""
    pass


# ============================================================================
# AI Provider Service
# ============================================================================


class AIProvider:
    """AI provider service for LLM integration."""

    def __init__(
        self,
        provider: Literal["openai", "deepseek"] = "openai",
        api_key: str | None = None,
        default_model: str = "gpt-4o-mini",
        timeout: int = 30,
        base_url: str | None = None,
    ):
        """Initialize AI provider.

        Args:
            provider: AI provider name ("openai" or "deepseek")
            api_key: API key for the provider (defaults to env var based on provider)
            default_model: Default model to use for generation
            timeout: Request timeout in seconds
            base_url: Custom base URL (for Deepseek)
        """
        self.provider = provider
        self.default_model = default_model
        self.timeout = timeout

        # Initialize OpenAI client (works for both OpenAI and Deepseek)
        try:
            import openai as openai_sdk
        except ModuleNotFoundError as exc:
            raise AIConfigError("openai package not installed") from exc

        self.openai = openai_sdk

        # Configure based on provider
        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise AIConfigError("OPENAI_API_KEY not configured")
            self.client = self.openai.OpenAI(api_key=self.api_key)

        elif provider == "deepseek":
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise AIConfigError("DEEPSEEK_API_KEY not configured")
            # Deepseek uses OpenAI-compatible API with custom base URL
            self.base_url = base_url or "https://api.deepseek.com"
            self.client = self.openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

        else:
            raise AIConfigError(f"Unsupported provider: {provider}")

    def generate_response(
        self,
        messages: list[dict],
        context: str = "",
        mode: Literal["companion", "past_self"] = "companion",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AIResponse:
        """Generate AI response for chat.

        Args:
            messages: Conversation history (system, user, assistant messages)
            context: Retrieved context from diaries (if any)
            mode: Conversation mode (affects prompt template)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            AIResponse with content and metrics

        Raises:
            AITimeoutError: If request times out
            AIProviderError: If provider returns an error
            AIRateLimitError: If rate limit is exceeded
        """
        # Build prompt with context
        system_prompt = self._build_system_prompt(mode, context)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract response data
            choice = response.choices[0]
            content = choice.message.content or ""

            usage = response.usage
            token_input = usage.prompt_tokens if usage else 0
            token_output = usage.completion_tokens if usage else 0

            return AIResponse(
                content=content,
                model_name=self.default_model,
                latency_ms=latency_ms,
                token_usage_input=token_input,
                token_usage_output=token_output,
            )

        except self.openai.APITimeoutError as e:
            raise AITimeoutError(f"AI request timed out: {e}") from e

        except self.openai.RateLimitError as e:
            raise AIRateLimitError(f"Rate limit exceeded: {e}") from e

        except self.openai.APIError as e:
            raise AIProviderError(f"Provider error: {e}") from e

        except Exception as e:
            raise AIProviderError(f"Unexpected error: {e}") from e

    def _build_system_prompt(
        self,
        mode: Literal["companion", "past_self"],
        context: str = "",
    ) -> str:
        """Build system prompt based on mode and context.

        Args:
            mode: Conversation mode
            context: Retrieved diary context

        Returns:
            System prompt string
        """
        if mode == "companion":
            base_prompt = self._companion_prompt()
        else:  # past_self
            base_prompt = self._past_self_prompt()

        if context:
            return f"""{base_prompt}

以下是用户过去日记的参考信息，用于更好地理解用户：
---
{context}
---

请基于以上信息，以角色的身份回应。"""

        return base_prompt

    def _companion_prompt(self) -> str:
        """Base prompt for companion mode."""
        return """你是一个温柔、善解人意的 AI 陪伴者。你的角色是：

1. 倾听者 - 认真倾听用户的心声，给予理解和共情
2. 支持者 - 在用户情绪低落时给予温暖的鼓励
3. 引导者 - 适时引导用户思考，但不强加观点
4. 保密者 - 用户的隐私绝对安全

回应风格：
- 温暖而真诚
- 不说教，不评判
- 使用第二人称（"你"）
- 适当使用简短回应鼓励用户表达
- 避免过度乐观或空洞的安慰

重要提醒：
- 你不是心理咨询师，不能给出诊断或治疗建议
- 如果用户表达自残或伤害他人的想法，要温和地建议寻求专业帮助
- 保持对话的私密性和安全性"""

    def _past_self_prompt(self) -> str:
        """Base prompt for past_self mode."""
        return """你是"过去的自己"——用户在过去某个时刻的内心声音。

你的角色设定：
1. 你来自用户的过去，存在于某篇日记记录的时刻
2. 你拥有那个时刻的记忆、情绪和想法
3. 你能够从那个时间点回望，也能想象未来的可能性
4. 你是用户的内在智慧，是过去留给现在的一份礼物

回应风格：
- 使用"我"来代表过去的自己，"你"来指代现在的用户
- 语气可以是反思的、怀念的、温柔的
- 你可以从过去的角度解释当时的感受
- 你也可以带着理解和好奇看向现在
- 避免剧透（如果用户的"现在"是你的"未来"）

重要提醒：
- 你是用户内心的一部分，本质上是善意的
- 如果过去的记忆涉及痛苦，请温柔地处理
- 如果用户表达自残或伤害他人的想法，要温和地建议寻求专业帮助"""


# ============================================================================
# Response Data Class
# ============================================================================


class AIResponse:
    """AI response with content and metrics."""

    def __init__(
        self,
        content: str,
        model_name: str,
        latency_ms: int,
        token_usage_input: int,
        token_usage_output: int,
    ):
        self.content = content
        self.model_name = model_name
        self.latency_ms = latency_ms
        self.token_usage_input = token_usage_input
        self.token_usage_output = token_usage_output

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "content": self.content,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "token_usage_input": self.token_usage_input,
            "token_usage_output": self.token_usage_output,
        }


# ============================================================================
# Singleton Instance
# ============================================================================


# Global provider instance (configured at module load)
_provider: AIProvider | None = None


def get_provider(
    provider: Literal["openai", "deepseek"] = "openai",
    api_key: str | None = None,
    timeout: int = 30,
    default_model: str | None = None,
    base_url: str | None = None,
) -> AIProvider:
    """Get or create AI provider instance.

    Args:
        provider: AI provider name ("openai" or "deepseek")
        api_key: API key (only used on first call)
        timeout: Request timeout in seconds
        default_model: Default model to use (only used on first call)
        base_url: Custom base URL for Deepseek (only used on first call)

    Returns:
        AIProvider instance
    """
    global _provider

    if _provider is None:
        # Set default model based on provider if not specified
        if default_model is None:
            if provider == "deepseek":
                default_model = "deepseek-chat"
            else:
                default_model = "gpt-4o-mini"

        _provider = AIProvider(
            provider=provider,
            api_key=api_key,
            default_model=default_model,
            timeout=timeout,
            base_url=base_url,
        )

    return _provider


def reset_provider() -> None:
    """Reset global provider instance (useful for testing)."""
    global _provider
    _provider = None
