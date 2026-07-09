"""Schemas for AI image generation API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """Request schema for image generation."""

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="Description of the desired image. Must be between 10-4000 characters.",
    )
    emotion: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional emotion to influence image style (e.g., 'calm', 'joyful', 'melancholy')",
    )
    provider: Optional[Literal["openai", "volces"]] = Field(
        default="openai",
        description="AI provider for image generation",
    )
    style: Optional[Literal["vivid", "natural"]] = Field(
        default="vivid",
        description="Image style for DALL-E 3: 'vivid' for hyper-realistic, 'natural' for more realistic",
    )
    size: Optional[Literal["1024x1024", "1792x1024", "1024x1792", "2K"]] = Field(
        default="1024x1024",
        description="Image size in pixels (2K for Volces Ark)",
    )
    quality: Optional[Literal["standard", "hd"]] = Field(
        default="standard",
        description="Image quality: 'standard' or 'hd' (DALL-E 3 only)",
    )
    model: Optional[Literal["dall-e-3", "dall-e-2", "doubao-seedream-5-0-260128"]] = Field(
        default="dall-e-3",
        description="Image generation model",
    )
    watermark: Optional[bool] = Field(
        default=False,
        description="Whether to add watermark to generated image (Volces Ark only)",
    )


class ImageGenerationResponse(BaseModel):
    """Response schema for image generation."""

    id: int = Field(description="Uploaded asset ID")
    image_url: str = Field(description="Public URL of the generated image")
    prompt_used: str = Field(description="The actual prompt used for generation (may be revised)")
    revised_prompt: Optional[str] = Field(default=None, description="DALL-E revised prompt if available")
    model: str = Field(description="Model used for generation")
    size: str = Field(description="Image size")
    generation_time_ms: int = Field(description="Time taken to generate image in milliseconds")
    created_at: datetime = Field(description="Timestamp when image was created")


class ImageGenerationErrorResponse(BaseModel):
    """Error response schema for image generation."""

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
