"""
Audio upload and transcription endpoints for voice input functionality.
"""
import base64
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.audio import (
    AudioUploadRequest,
    AudioUploadResponse,
    AudioTranscribeRequest,
    AudioTranscribeResponse,
)
from ..schemas.common import ApiResponse

router = APIRouter()

# Audio upload directory
AUDIO_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads" / "audio"
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum audio file size: 25MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024

# Supported audio formats
SUPPORTED_FORMATS = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/mp3": ".mp3",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}


def extract_duration_from_data_url(data_url: str) -> Optional[float]:
    """
    Extract duration from audio data URL if available.
    This is a placeholder - real implementation would parse audio metadata.
    """
    # TODO: Implement audio metadata parsing to get actual duration
    # For now, return None (duration will be estimated from file size)
    return None


def estimate_duration_from_size(file_size: int, content_type: str) -> float:
    """
    Estimate audio duration from file size and content type.
    This is a rough approximation.
    """
    # Rough bitrate estimates (bits per second)
    bitrate_map = {
        "audio/webm": 64000,  # 64 kbps
        "audio/ogg": 64000,
        "audio/wav": 128000,  # 128 kbps
        "audio/mp3": 128000,
        "audio/mpeg": 128000,
        "audio/mp4": 96000,
        "audio/x-m4a": 96000,
    }
    bitrate = bitrate_map.get(content_type, 64000)
    # Duration (seconds) = (file_size * 8) / bitrate
    return (file_size * 8) / bitrate


@router.post("/audio/upload", response_model=ApiResponse[AudioUploadResponse])
async def upload_audio(
    request: AudioUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload an audio file for voice input.

    The audio file is sent as a base64-encoded data URL.
    Supports formats: webm, ogg, wav, mp3, m4a
    Maximum file size: 25MB

    Returns the URL where the audio can be accessed.
    """
    try:
        # Validate content type
        if request.content_type not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {request.content_type}. "
                f"Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
            )

        # Parse data URL
        if not request.data_url.startswith(f"data:{request.content_type};base64,"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data URL format. Expected: data:{request.content_type};base64,..."
            )

        # Extract base64 data
        base64_data = request.data_url.split(",", 1)[1]
        audio_data = base64.b64decode(base64_data)

        # Check file size
        file_size = len(audio_data)
        if file_size > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE / 1024 / 1024:.1f}MB"
            )

        # Generate unique filename
        ext = SUPPORTED_FORMATS[request.content_type]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"audio_{timestamp}_{unique_id}{ext}"
        file_path = AUDIO_UPLOAD_DIR / safe_filename

        # Save audio file
        with open(file_path, "wb") as f:
            f.write(audio_data)

        # Get or estimate duration
        duration = extract_duration_from_data_url(request.data_url)
        if duration is None:
            duration = estimate_duration_from_size(file_size, request.content_type)

        # Construct response
        audio_url = f"/uploads/audio/{safe_filename}"

        return ApiResponse(
            data=AudioUploadResponse(
                audio_url=audio_url,
                duration=round(duration, 2),
                file_size=file_size,
                filename=safe_filename
            ),
            message="音频上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频上传失败: {str(e)}")


@router.post("/audio/transcribe", response_model=ApiResponse[AudioTranscribeResponse])
async def transcribe_audio(
    request: AudioTranscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Transcribe audio to text using STT service.

    This endpoint is currently a placeholder that returns mock transcription.
    To enable real transcription:
    1. Configure STT provider credentials (Azure Speech, Google Cloud STT, OpenAI Whisper, etc.)
    2. Update this endpoint to call the STT service
    3. Process the audio file and return actual transcription

    For now, the frontend uses Web Speech API for real-time transcription.
    This endpoint is reserved for future server-side transcription needs.
    """
    try:
        # TODO: Implement actual STT service integration
        # Options:
        # - Azure Speech Service
        # - Google Cloud Speech-to-Text
        # - OpenAI Whisper API
        # - Local Whisper model

        # Placeholder response
        return ApiResponse(
            data=AudioTranscribeResponse(
                text="音频转录功能待实现。请使用浏览器语音输入作为替代方案。",
                confidence=0.0,
                language=request.language or "zh-CN",
                duration=None,
                provider=None
            ),
            message="音频转录为预留功能，当前返回模拟数据"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频转录失败: {str(e)}")


@router.get("/audio/formats")
async def get_supported_formats():
    """
    Get list of supported audio formats for upload.
    """
    return ApiResponse(
        data={
            "formats": list(SUPPORTED_FORMATS.keys()),
            "max_size_mb": MAX_AUDIO_SIZE / 1024 / 1024,
            "description": "支持的音频格式和文件大小限制"
        }
    )
