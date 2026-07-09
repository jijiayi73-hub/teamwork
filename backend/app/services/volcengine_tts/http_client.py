"""
Volcengine TTS HTTP Unidirectional Client

火山引擎豆包单向流式语音合成HTTP客户端实现。

使用 HTTP POST 请求进行一次性文本转语音，返回完整音频数据。
适合短文本合成场景。

Reference: https://www.volcengine.com/docs/6561/1719100
"""

import asyncio
import base64
import json
import logging
from typing import Optional, AsyncIterator
import aiohttp
from .models import TTSConfig, DEFAULT_BROWSER_CONFIG
from .exceptions import VolcengineTTSError, ConnectionError as TTSConnectionError

logger = logging.getLogger(__name__)


class VolcengineTTSHttpClient:
    """
    Volcengine TTS HTTP Unidirectional Client

    使用 HTTP POST 请求进行文本转语音。
    适合一次性合成短文本的场景。
    """

    def __init__(
        self,
        api_key: str,
        resource_id: str = "volc.service_type.10029",
        endpoint: str = "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
        config: Optional[TTSConfig] = None,
    ):
        """
        Initialize TTS HTTP client.

        Args:
            api_key: API Key for authentication
            resource_id: Resource ID (e.g., "volc.service_type.10029")
            endpoint: HTTP endpoint URL
            config: TTS configuration
        """
        self.api_key = api_key
        self.resource_id = resource_id
        self.endpoint = endpoint
        self.config = config or TTSConfig(**DEFAULT_BROWSER_CONFIG)

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def synthesize(
        self,
        text: str,
        speaker: Optional[str] = None,
        format: str = "mp3",
        sample_rate: int = 24000,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Input text to synthesize
            speaker: Speaker voice name (optional, uses config default if not specified)
            format: Audio format (mp3, wav, opus)
            sample_rate: Sample rate (16000, 24000, 48000)
            speed: Speech speed (0.2 - 2.0)
            volume: Volume gain (-96 to 16)

        Returns:
            Audio data as bytes

        Raises:
            TTSConnectionError: If HTTP request fails
            VolcengineTTSError: If TTS synthesis fails
        """
        speaker = speaker or self.config.speaker

        # Build request payload
        payload = {
            "req_params": {
                "text": text,
                "speaker": speaker,
                "audio_params": {
                    "format": format,
                    "sample_rate": sample_rate,
                },
                "speed": speed,
                "volume": volume,
            },
            "additions": '{"disable_markdown_filter":true}',
        }

        # Build headers
        headers = {
            "x-api-key": self.api_key,
            "X-Api-Resource-Id": self.resource_id,
            "Content-Type": "application/json",
        }

        session = await self._get_session()

        try:
            async with session.post(
                self.endpoint,
                headers=headers,
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"TTS HTTP request failed: {response.status} - {error_text}")
                    raise TTSConnectionError(
                        f"HTTP request failed with status {response.status}: {error_text}"
                    )

                content_type = response.headers.get("Content-Type", "")

                # Check if response is JSON (base64 encoded audio) or binary audio
                if "application/json" in content_type:
                    data = await response.json()

                    if data.get("code") != 0:
                        error_msg = data.get("message", "Unknown error")
                        error_code = data.get("code")
                        raise VolcengineTTSError(
                            f"TTS synthesis failed (code={error_code}): {error_msg}",
                            code=error_code,
                        )

                    # Decode base64 audio data
                    audio_data_str = data.get("data")
                    if not audio_data_str:
                        raise VolcengineTTSError("No audio data in response")

                    audio_data = base64.b64decode(audio_data_str)
                    return audio_data

                elif "audio" in content_type or "octet-stream" in content_type:
                    # Binary audio data
                    return await response.read()
                else:
                    # Try to parse as JSON
                    text_data = await response.text()
                    try:
                        data = json.loads(text_data)
                        if data.get("code") != 0:
                            raise VolcengineTTSError(
                                f"TTS synthesis failed: {data.get('message', 'Unknown error')}"
                            )
                    except json.JSONDecodeError:
                        pass

                    # Return as-is
                    return text_data.encode("utf-8")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise TTSConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise VolcengineTTSError(f"TTS synthesis failed: {e}")

    async def synthesize_streaming(
        self,
        text: str,
        speaker: Optional[str] = None,
        format: str = "mp3",
        sample_rate: int = 24000,
        speed: float = 1.0,
        volume: float = 1.0,
        chunk_size: int = 4096,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize speech from text, yielding audio chunks.

        This is a compatibility method for streaming interface.
        Since HTTP unidirectional returns complete audio,
        this yields the complete audio in chunks.

        Args:
            text: Input text to synthesize
            speaker: Speaker voice name
            format: Audio format
            sample_rate: Sample rate
            speed: Speech speed
            volume: Volume gain
            chunk_size: Size of chunks to yield

        Yields:
            Audio data chunks
        """
        audio_data = await self.synthesize(
            text=text,
            speaker=speaker,
            format=format,
            sample_rate=sample_rate,
            speed=speed,
            volume=volume,
        )

        # Yield audio in chunks
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
