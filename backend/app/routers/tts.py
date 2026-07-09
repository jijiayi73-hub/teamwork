"""
Volcengine TTS WebSocket Router

FastAPI WebSocket端点，为前端提供TTS流式音频服务。

Protocol:
1. Frontend connects via WebSocket
2. Frontend sends control messages (start, text, finish, cancel)
3. Backend forwards to Volcengine TTS
4. Backend streams audio back to frontend
5. Connection is kept alive for multiple sessions

WebSocket Message Format (JSON):
- Client → Server: {"type": "start|text|finish|cancel", "text": "...", "speaker": "..."}
- Server → Client: {"type": "session_started|sentence_start|sentence_end|finished|error", ...}
- Audio: Binary frames (PCM audio data)
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.volcengine_tts import (
    VolcengineTTSClient,
    TTSConfig,
    TTSConnectionError,
    AuthenticationError,
    SessionError,
    TimeoutError,
    get_error_message,
)
from app.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["TTS"])


# Pydantic models for WebSocket messages
class TTSSessionRequest(BaseModel):
    speaker: Optional[str] = None
    format: Optional[str] = "pcm"
    sample_rate: Optional[int] = 24000


class TTSTextRequest(BaseModel):
    text: str


class TTSControlMessage(BaseModel):
    type: str  # "start", "text", "finish", "cancel"
    text: Optional[str] = None
    speaker: Optional[str] = None
    format: Optional[str] = None
    sample_rate: Optional[int] = None


@router.get("/tts/health")
async def tts_health_check():
    """Check if TTS service is configured."""
    return {
        "success": True,
        "data": {
            "enabled": bool(settings.volcengine_tts_api_key),
            "speaker": settings.volcengine_tts_speaker,
            "resource_id": settings.volcengine_tts_resource_id,
        }
    }


@router.get("/tts/speakers")
async def list_speakers():
    """List available TTS speakers."""
    from app.services.volcengine_tts import POPULAR_SPEAKERS
    return {
        "success": True,
        "data": {
            "speakers": POPULAR_SPEAKERS,
            "default": settings.volcengine_tts_speaker,
        }
    }


@router.websocket("/api/v1/tts/stream")
async def tts_websocket(websocket: WebSocket):
    """
    TTS streaming WebSocket endpoint.

    Connection flow:
    1. Client sends: {"type": "start", "speaker": "...", "format": "..."}
    2. Server replies: {"type": "session_started", "session_id": "..."}
    3. Client sends: {"type": "text", "text": "..."}
    4. Server sends: {"type": "sentence_start", "text": "..."}
    5. Server sends: binary audio frames
    6. Server sends: {"type": "sentence_end", "text": "..."}
    7. Client sends: {"type": "finish"}
    8. Server sends: {"type": "finished", "usage": {...}}

    Error handling:
    - Server sends: {"type": "error", "message": "...", "code": "..."}
    - Connection closes on fatal errors
    """
    # Check if TTS is configured
    if not settings.volcengine_tts_api_key:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "TTS service is not configured. Please set VOLCENGINE_TTS_API_KEY.",
            "code": "not_configured"
        })
        await websocket.close()
        return

    # Accept WebSocket connection
    await websocket.accept()

    # TTS client instance
    tts_client: Optional[VolcengineTTSClient] = None
    session_active = False

    try:
        # Initialize TTS client
        tts_client = VolcengineTTSClient(
            api_key=settings.volcengine_tts_api_key,
            resource_id=settings.volcengine_tts_resource_id,
            endpoint=settings.volcengine_tts_endpoint,
            app_id=settings.volcengine_tts_app_id or None,
            access_key=settings.volcengine_tts_access_key or None,
        )

        # Connect to Volcengine
        logger.info("Connecting to Volcengine TTS...")
        await tts_client.connect()
        logger.info(f"Connected: {tts_client.connection_id}")

        await websocket.send_json({
            "type": "connection_started",
            "connection_id": tts_client.connection_id,
        })

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive()

            if "text" in data:
                # JSON control message
                try:
                    message = TTSControlMessage.model_validate_json(data["text"])
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Invalid message format: {e}",
                        "code": "invalid_format"
                    })
                    continue

                # Handle different message types
                if message.type == "start":
                    if session_active:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Session already active",
                            "code": "session_exists"
                        })
                        continue

                    # Build TTS config
                    config = TTSConfig(
                        speaker=message.speaker or settings.volcengine_tts_speaker,
                        format=message.format or "pcm",
                        sample_rate=message.sample_rate or 24000,
                    )

                    # Start session
                    session_id = await tts_client.start_session()
                    session_active = True

                    await websocket.send_json({
                        "type": "session_started",
                        "session_id": session_id,
                    })
                    logger.info(f"Session started: {session_id}")

                elif message.type == "text":
                    if not session_active:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No active session",
                            "code": "no_session"
                        })
                        continue

                    if not message.text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Text is required",
                            "code": "missing_text"
                        })
                        continue

                    # Send text and stream audio
                    try:
                        async for audio_chunk in tts_client.send_text(message.text):
                            # Send binary audio directly
                            await websocket.send_bytes(audio_chunk)

                    except Exception as e:
                        logger.error(f"Error streaming audio: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                            "code": "stream_error"
                        })

                elif message.type == "finish":
                    if not session_active:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No active session",
                            "code": "no_session"
                        })
                        continue

                    # Finish session
                    usage = await tts_client.finish_session()
                    session_active = False

                    await websocket.send_json({
                        "type": "finished",
                        "usage": {
                            "text_words": usage.text_words if usage else 0
                        } if usage else None
                    })
                    logger.info("Session finished")

                elif message.type == "cancel":
                    if not session_active:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No active session",
                            "code": "no_session"
                        })
                        continue

                    # Cancel session
                    await tts_client.cancel_session()
                    session_active = False

                    await websocket.send_json({
                        "type": "canceled",
                    })
                    logger.info("Session canceled")

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message.type}",
                        "code": "unknown_type"
                    })

            elif "bytes" in data:
                # Binary data from client (not expected, ignore)
                logger.warning("Received unexpected binary data from client")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except TTSConnectionError as e:
        logger.error(f"Connection error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {e.message}",
                "code": "connection_error"
            })
        except Exception:
            pass
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed. Check API credentials.",
                "code": "auth_error"
            })
        except Exception:
            pass
    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Operation timed out",
                "code": "timeout"
            })
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "code": "unexpected_error"
            })
        except Exception:
            pass
    finally:
        # Clean up
        if tts_client:
            try:
                await tts_client.close()
            except Exception as e:
                logger.error(f"Error closing TTS client: {e}")
        logger.info("TTS WebSocket connection closed")
