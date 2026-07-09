"""Image generation router for AI-powered cover image creation.

Provides POST /api/v1/generate-image endpoint for generating
AI images using DALL-E and persisting them to the uploads directory.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import User
from ..schemas.common import ApiResponse, ErrorCode, ErrorResponse
from ..schemas.images import (
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from ..services.image_generation_service import ImageGenerationService


router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "/generate",
    response_model=ApiResponse[ImageGenerationResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
def generate_image(
    request: ImageGenerationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI image using DALL-E.

    Creates a new image based on the provided prompt and emotion context.
    The image is automatically saved to the uploads directory and an
    asset record is created.

    Args:
        request: Image generation request with prompt and parameters
        user: Current authenticated user
        db: Database session

    Returns:
        ImageGenerationResponse with image URL and metadata

    Raises:
        401: Not authenticated
        429: Rate limit exceeded (from OpenAI)
        502: AI provider error
        504: AI timeout
        500: Internal server error
    """
    service = ImageGenerationService(db)
    response_data, status_code = service.generate_cover_image(request, user)

    if status_code != 200:
        from fastapi.responses import JSONResponse
        from fastapi.encoders import jsonable_encoder

        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(response_data),
        )

    return ApiResponse(data=response_data, message="image_generated")
