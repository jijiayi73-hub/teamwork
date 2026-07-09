"""Tests for image generation service and API."""
from __future__ import annotations

import base64
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models import UploadedAsset, User
from app.schemas.images import ImageGenerationRequest
from app.services.ai_provider import AIImageResponse
from app.services.image_generation_service import ImageGenerationService


# ============================================================================
# Fixtures
# ============================================================================


def create_user(db_session, name: str = "imguser") -> User:
    """Helper to create a test user."""
    user = User(
        username=name,
        email=f"{name}@example.com",
        password_hash="hash",
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def image_gen_service(db_session):
    """Create image generation service fixture."""
    return ImageGenerationService(db_session)


@pytest.fixture
def test_user_obj(db_session):
    """Create a test user in database."""
    return create_user(db_session)


@pytest.fixture
def valid_image_request():
    """Create valid image generation request."""
    return ImageGenerationRequest(
        prompt="Soft watercolor garden scene with calm emotions",
        emotion="calm",
        style="vivid",
        size="1024x1024",
        quality="standard",
        model="dall-e-3",
    )


@pytest.fixture
def mock_ai_image_response():
    """Create mock AI image response."""
    return AIImageResponse(
        image_url="https://mock.openai.com/images/abc123.png",
        revised_prompt="Soft watercolor garden scene with calm emotions and gentle light",
        model_name="dall-e-3",
        latency_ms=3500,
    )


@pytest.fixture
def sample_png_bytes():
    """Create sample PNG bytes."""
    # Minimal valid PNG
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )


# ============================================================================
# Prompt Building Tests
# ============================================================================


class TestPromptBuilding:
    """Tests for _build_prompt method."""

    def test_build_prompt_with_emotion(self, image_gen_service):
        """Test prompt building with emotion context."""
        result = image_gen_service._build_prompt("A garden scene", "calm")
        # Emotion is converted to style description
        assert "peaceful" in result.lower() or "calm" in result.lower()
        assert "garden scene" in result.lower()
        assert "watercolor" in result.lower()

    def test_build_prompt_with_joy_emotion(self, image_gen_service):
        """Test prompt building with joy emotion."""
        result = image_gen_service._build_prompt("A happy memory", "joy")
        # Joy is converted to warm/bright style description
        assert "warm" in result.lower() or "bright" in result.lower()
        assert "watercolor" in result.lower()

    def test_build_prompt_without_emotion(self, image_gen_service):
        """Test prompt building without emotion."""
        result = image_gen_service._build_prompt("A simple scene", None)
        assert "simple scene" in result.lower()
        assert "watercolor" in result.lower()


# ============================================================================
# Image Generation Tests
# ============================================================================


class TestImageGeneration:
    """Tests for generate_cover_image method."""

    @patch("app.services.image_generation_service.get_provider")
    @patch.object(ImageGenerationService, "_download_image")
    def test_generate_image_success(
        self,
        mock_download,
        mock_get_provider,
        image_gen_service,
        valid_image_request,
        test_user_obj,
        mock_ai_image_response,
        sample_png_bytes,
    ):
        """Test successful image generation."""
        # Setup mocks - provider must have provider attribute set to "openai"
        from app.services.ai_provider import AIProvider

        mock_provider = Mock(spec=AIProvider)
        mock_provider.provider = "openai"
        mock_provider.generate_image.return_value = mock_ai_image_response
        mock_get_provider.return_value = mock_provider
        mock_download.return_value = sample_png_bytes

        # Execute
        response, status_code = image_gen_service.generate_cover_image(
            valid_image_request, test_user_obj
        )

        # Verify
        assert status_code == 200
        assert response.image_url.startswith("/uploads/")
        assert response.model == "dall-e-3"
        assert response.size == "1024x1024"
        assert response.generation_time_ms > 0

        # Verify provider was called correctly
        mock_provider.generate_image.assert_called_once()

    @patch("app.services.image_generation_service.get_provider")
    def test_generate_image_with_unsupported_provider(
        self,
        mock_get_provider,
        image_gen_service,
        valid_image_request,
        test_user_obj,
    ):
        """Test image generation with non-OpenAI provider."""
        # Setup: make generate_image raise AIConfigError
        from app.services.ai_provider import AIConfigError, AIProvider

        mock_provider = Mock(spec=AIProvider)
        # Simulate what happens when provider is not OpenAI
        mock_provider.generate_image.side_effect = AIConfigError(
            "Image generation is only supported for OpenAI provider"
        )
        mock_get_provider.return_value = mock_provider

        # Execute
        response, status_code = image_gen_service.generate_cover_image(
            valid_image_request, test_user_obj
        )

        # Verify error response
        assert status_code == 500
        assert response["error"] == "config_error"

    @patch("app.services.image_generation_service.get_provider")
    def test_generate_image_timeout(
        self,
        mock_get_provider,
        image_gen_service,
        valid_image_request,
        test_user_obj,
    ):
        """Test image generation timeout handling."""
        # Setup mock to raise timeout
        from app.services.ai_provider import AITimeoutError

        mock_provider = Mock()
        mock_provider.provider = "openai"
        mock_provider.generate_image.side_effect = AITimeoutError("Request timed out")
        mock_get_provider.return_value = mock_provider

        # Execute
        response, status_code = image_gen_service.generate_cover_image(
            valid_image_request, test_user_obj
        )

        # Verify error response
        assert status_code == 504
        assert response["error"] == "timeout"

    @patch("app.services.image_generation_service.get_provider")
    def test_generate_image_rate_limit(
        self,
        mock_get_provider,
        image_gen_service,
        valid_image_request,
        test_user_obj,
    ):
        """Test image generation rate limit handling."""
        # Setup mock to raise rate limit error
        from app.services.ai_provider import AIRateLimitError

        mock_provider = Mock()
        mock_provider.provider = "openai"
        mock_provider.generate_image.side_effect = AIRateLimitError("Rate limit exceeded")
        mock_get_provider.return_value = mock_provider

        # Execute
        response, status_code = image_gen_service.generate_cover_image(
            valid_image_request, test_user_obj
        )

        # Verify error response
        assert status_code == 429
        assert response["error"] == "rate_limit"


# ============================================================================
# API Router Tests
# ============================================================================


class TestImageGenerationAPI:
    """Tests for image generation API endpoint."""

    def test_generate_image_endpoint_requires_auth(self, client):
        """Test that endpoint requires authentication."""
        response = client.post(
            "/api/v1/images/generate",
            json={
                "prompt": "Test prompt that is long enough",
                "emotion": "calm",
            },
        )
        assert response.status_code == 401

    @patch("app.services.image_generation_service.get_provider")
    @patch.object(ImageGenerationService, "_download_image")
    def test_generate_image_endpoint_success(
        self,
        mock_download,
        mock_get_provider,
        client,
        auth_headers,
        mock_ai_image_response,
        sample_png_bytes,
    ):
        """Test successful API call."""
        # Setup mocks
        mock_provider = Mock()
        mock_provider.provider = "openai"
        mock_provider.generate_image.return_value = mock_ai_image_response
        mock_get_provider.return_value = mock_provider
        mock_download.return_value = sample_png_bytes

        # Execute
        response = client.post(
            "/api/v1/images/generate",
            headers=auth_headers,
            json={
                "prompt": "Soft watercolor garden scene with calm emotions",
                "emotion": "calm",
                "size": "1024x1024",
            },
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "image_generated"
        assert "data" in data
        assert data["data"]["model"] == "dall-e-3"

    def test_generate_image_endpoint_validation(self, client, auth_headers):
        """Test request validation."""
        # Test with too short prompt
        response = client.post(
            "/api/v1/images/generate",
            headers=auth_headers,
            json={
                "prompt": "short",  # Too short (< 10 chars)
                "emotion": "calm",
            },
        )
        assert response.status_code == 422

        # Test with invalid size
        response = client.post(
            "/api/v1/images/generate",
            headers=auth_headers,
            json={
                "prompt": "A valid prompt that is long enough",
                "size": "9999x9999",  # Invalid size
            },
        )
        assert response.status_code == 422


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestImageGenerationSchemas:
    """Tests for image generation schemas."""

    def test_valid_image_generation_request(self):
        """Test valid request schema."""
        request = ImageGenerationRequest(
            prompt="A beautiful watercolor garden scene",
            emotion="calm",
            style="vivid",
            size="1024x1024",
            quality="standard",
            model="dall-e-3",
        )
        assert request.prompt == "A beautiful watercolor garden scene"
        assert request.emotion == "calm"
        assert request.model == "dall-e-3"

    def test_minimal_request_schema(self):
        """Test minimal valid request."""
        request = ImageGenerationRequest(
            prompt="A scene description that meets the minimum length requirement"
        )
        assert request.prompt is not None
        assert request.style == "vivid"  # Default value
        assert request.size == "1024x1024"  # Default value

    def test_request_prompt_too_short(self):
        """Test validation rejects short prompts."""
        with pytest.raises(Exception):
            ImageGenerationRequest(prompt="short")

    def test_request_prompt_too_long(self):
        """Test validation rejects long prompts."""
        with pytest.raises(Exception):
            ImageGenerationRequest(prompt="x" * 4001)

    def test_invalid_size_enum(self):
        """Test validation rejects invalid sizes."""
        with pytest.raises(Exception):
            ImageGenerationRequest(
                prompt="A valid prompt description",
                size="512x512",  # Not in allowed enum
            )

    def test_invalid_model_enum(self):
        """Test validation rejects invalid models."""
        with pytest.raises(Exception):
            ImageGenerationRequest(
                prompt="A valid prompt description",
                model="dall-e-1",  # Not supported
            )
