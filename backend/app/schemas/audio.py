"""
Audio-related schemas for voice input functionality.
"""
from pydantic import BaseModel, Field
from typing import Optional


class AudioUploadRequest(BaseModel):
    """Request schema for audio file upload."""
    filename: str = Field(..., description="Audio filename with extension")
    content_type: str = Field(..., description="MIME type (e.g., audio/webm, audio/wav, audio/mp3)")
    data_url: str = Field(..., description="Base64-encoded data URL (data:audio/...;base64,...)")


class AudioUploadResponse(BaseModel):
    """Response schema for successful audio upload."""
    audio_url: str = Field(..., description="URL to access the uploaded audio file")
    duration: Optional[float] = Field(None, description="Audio duration in seconds (if available)")
    file_size: int = Field(..., description="File size in bytes")
    filename: str = Field(..., description="Stored filename")


class AudioTranscribeRequest(BaseModel):
    """Request schema for audio transcription."""
    audio_url: str = Field(..., description="URL of the audio file to transcribe")
    language: Optional[str] = Field("zh-CN", description="Source language code (default: zh-CN)")
    provider: Optional[str] = Field(None, description="STT provider to use (e.g., azure, google, whisper)")


class AudioTranscribeResponse(BaseModel):
    """Response schema for audio transcription."""
    text: str = Field(..., description="Transcribed text content")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    language: str = Field(..., description="Detected or confirmed language code")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    provider: Optional[str] = Field(None, description="STT provider used")
