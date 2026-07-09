"""Image generation service for AI-powered cover image creation.

This service handles:
- AI image generation via DALL-E
- Image downloading and persistence
- Asset record creation
- Error handling and logging
"""
from __future__ import annotations

import httpx
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from ..config import settings
from ..models import UploadedAsset, User
from ..services.ai_provider import (
    AIConfigError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    get_provider,
)
from ..schemas.images import ImageGenerationRequest, ImageGenerationResponse


class ImageGenerationService:
    """Service for generating and storing AI-generated images."""

    def __init__(self, db: Session):
        """Initialize image generation service.

        Args:
            db: Database session
        """
        self.db = db
        self.upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.public_prefix = "/uploads"

    def generate_cover_image(
        self,
        request: ImageGenerationRequest,
        user: User,
    ) -> tuple[ImageGenerationResponse | dict, int]:
        """Generate a cover image using AI.

        Args:
            request: Image generation request
            user: Current user

        Returns:
            Tuple of (response data, HTTP status code)

        Raises:
            No explicit raises - returns error dict with status code
        """
        start_time = time.time()

        # Build enhanced prompt with emotion context
        enhanced_prompt = self._build_prompt(request.prompt, request.emotion)

        try:
            # Determine the provider to use
            provider_name = request.provider if hasattr(request, 'provider') else settings.ai_provider

            # Select the appropriate model based on provider
            if provider_name == "volces":
                model_to_use = request.model if hasattr(request, 'model') and request.model.startswith("doubao-") else settings.volces_image_model
                base_url = settings.volces_base_url
            elif provider_name == "openai":
                model_to_use = request.model if hasattr(request, 'model') else settings.ai_default_model
                base_url = None
            else:
                # For other providers (like deepseek), image generation is not supported
                model_to_use = settings.ai_default_model
                base_url = settings.deepseek_base_url if settings.ai_provider == "deepseek" else None

            provider = get_provider(
                provider=provider_name,
                default_model=model_to_use,
                timeout=settings.ai_timeout,
                base_url=base_url,
            )

            ai_response = provider.generate_image(
                prompt=enhanced_prompt,
                size=request.size,
                model=model_to_use,
                quality=request.quality,
                style=request.style,
                watermark=request.watermark if hasattr(request, 'watermark') else False,
            )

            # Download and save the image
            image_bytes = self._download_image(ai_response.image_url)
            filename = self._save_image(user.id, image_bytes, request.size)

            # Create asset record
            asset = UploadedAsset(
                user_id=user.id,
                original_filename=f"ai-generated-{uuid4().hex[:8]}.png",
                stored_filename=filename,
                content_type="image/png",
                url=f"{self.public_prefix}/{filename}",
            )
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return (
                ImageGenerationResponse(
                    id=asset.id,
                    image_url=asset.url,
                    prompt_used=enhanced_prompt,
                    revised_prompt=ai_response.revised_prompt,
                    model=ai_response.model_name,
                    size=request.size,
                    generation_time_ms=generation_time_ms,
                    created_at=asset.created_at,
                ),
                200,
            )

        except AIConfigError as e:
            return {"error": "config_error", "message": str(e)}, 500

        except AITimeoutError as e:
            return {"error": "timeout", "message": "Image generation timed out. Please try again."}, 504

        except AIRateLimitError as e:
            return {"error": "rate_limit", "message": "Too many requests. Please wait and try again."}, 429

        except AIProviderError as e:
            return {"error": "provider_error", "message": f"Failed to generate image: {str(e)}"}, 502

        except Exception as e:
            return {"error": "internal_error", "message": f"Unexpected error: {str(e)}"}, 500

    def _build_prompt(self, base_prompt: str, emotion: str | None) -> str:
        """Build enhanced prompt with context.

        Args:
            base_prompt: User-provided prompt
            emotion: Optional emotion for style guidance

        Returns:
            Enhanced prompt with style guidance
        """
        # Add watercolor/therapeutic style prefix for emotional context
        if emotion:
            emotion_guidance = {
                "calm": "Soft, peaceful watercolor style with gentle blues and greens",
                "joy": "Bright, warm watercolor style with vibrant yellows and oranges",
                "sadness": "Muted, melancholic watercolor style with soft grays and purples",
                "anxiety": "Turbulent but controlled watercolor style with swirling patterns",
                "anger": "Intense, expressive watercolor style with bold reds and oranges",
                "fear": "Dark, moody watercolor style with shadows and contrast",
                "neutral": "Balanced, serene watercolor style",
            }
            style_prefix = emotion_guidance.get(emotion.lower(), "Therapeutic watercolor style")
            return f"{style_prefix}: {base_prompt}"

        return f"Soft therapeutic watercolor style: {base_prompt}"

    def _download_image(self, url: str) -> bytes:
        """Download image from URL.

        Args:
            url: Image URL

        Returns:
            Image bytes

        Raises:
            Exception: If download fails
        """
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def _save_image(self, user_id: int, image_bytes: bytes, size: str) -> str:
        """Save image to uploads directory.

        Args:
            user_id: User ID for namespacing
            image_bytes: Image data
            size: Image size (for potential filename hint)

        Returns:
            Stored filename
        """
        # Generate unique filename
        filename = f"{user_id}-ai-{uuid4().hex}.png"
        filepath = self.upload_dir / filename

        # Write image bytes
        with filepath.open("wb") as f:
            f.write(image_bytes)

        return filename
