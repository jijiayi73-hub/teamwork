"""
Volcengine TTS Service Package

火山引擎豆包双向流式语音合成服务模块。

Usage:
    from app.services.volcengine_tts import VolcengineTTSClient, TTSConfig

    client = VolcengineTTSClient(
        api_key="your-api-key",
        resource_id="seed-tts-2.0",
    )
    await client.connect()
    session_id = await client.start_session()
    async for audio_chunk in client.send_text("你好，世界"):
        # Process audio chunk
        pass
    await client.finish_session()
    await client.close()
"""

from .client import VolcengineTTSClient
from .models import (
    TTSConfig,
    TTSRequest,
    TTSResponse,
    TTSChunk,
    SessionInfo,
    TTSUsage,
    AudioFormat,
    SampleRate,
    POPULAR_SPEAKERS,
    DEFAULT_BROWSER_CONFIG,
)
from .events import (
    START_CONNECTION,
    FINISH_CONNECTION,
    CONNECTION_STARTED,
    CONNECTION_FAILED,
    CONNECTION_FINISHED,
    START_SESSION,
    CANCEL_SESSION,
    FINISH_SESSION,
    SESSION_STARTED,
    SESSION_CANCELED,
    SESSION_FINISHED,
    SESSION_FAILED,
    TASK_REQUEST,
    TTS_SENTENCE_START,
    TTS_SENTENCE_END,
    TTS_RESPONSE,
    get_event_name,
)
from .exceptions import (
    VolcengineTTSError,
    ConnectionError as TTSConnectionError,
    AuthenticationError,
    SessionError,
    ProtocolError,
    TimeoutError,
    RateLimitError,
    ServerError,
    get_error_message,
)
from .protocol import build_frame, parse_frame, ParsedFrame


__all__ = [
    # Client
    "VolcengineTTSClient",
    # Models
    "TTSConfig",
    "TTSRequest",
    "TTSResponse",
    "TTSChunk",
    "SessionInfo",
    "TTSUsage",
    "AudioFormat",
    "SampleRate",
    "POPULAR_SPEAKERS",
    "DEFAULT_BROWSER_CONFIG",
    # Events
    "START_CONNECTION",
    "FINISH_CONNECTION",
    "CONNECTION_STARTED",
    "CONNECTION_FAILED",
    "CONNECTION_FINISHED",
    "START_SESSION",
    "CANCEL_SESSION",
    "FINISH_SESSION",
    "SESSION_STARTED",
    "SESSION_CANCELED",
    "SESSION_FINISHED",
    "SESSION_FAILED",
    "TASK_REQUEST",
    "TTS_SENTENCE_START",
    "TTS_SENTENCE_END",
    "TTS_RESPONSE",
    "get_event_name",
    # Exceptions
    "VolcengineTTSError",
    "TTSConnectionError",
    "AuthenticationError",
    "SessionError",
    "ProtocolError",
    "TimeoutError",
    "RateLimitError",
    "ServerError",
    "get_error_message",
    # Protocol
    "build_frame",
    "parse_frame",
    "ParsedFrame",
]
