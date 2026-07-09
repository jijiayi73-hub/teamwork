"""
Volcengine TTS WebSocket Client

火山引擎豆包双向流式语音合成WebSocket客户端实现。

Connection Flow:
1. Connect → StartConnection → ConnectionStarted
2. StartSession → SessionStarted
3. TaskRequest (per text) → TTSResponse (audio)
4. FinishSession → SessionFinished
5. (Optional) FinishConnection → ConnectionFinished

Reference: https://www.volcengine.com/docs/6561/79817
"""

import asyncio
import uuid
import logging
from typing import Optional, AsyncIterator, Callable
from .protocol import (
    build_frame,
    parse_frame,
    FULL_CLIENT_REQUEST,
    SERIALIZATION_JSON,
    COMPRESSION_NONE,
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
from .models import TTSConfig, SessionInfo, TTSUsage, DEFAULT_BROWSER_CONFIG
from .exceptions import (
    VolcengineTTSError,
    ConnectionError as TTSConnectionError,
    AuthenticationError,
    SessionError,
    ProtocolError,
    TimeoutError,
    get_error_message,
)

logger = logging.getLogger(__name__)


class VolcengineTTSClient:
    """
    Volcengine TTS WebSocket Client

    Manages WebSocket connection and session lifecycle for TTS.
    Supports streaming text input and audio output.
    """

    def __init__(
        self,
        api_key: str,
        resource_id: str = "seed-tts-2.0",
        endpoint: str = "wss://openspeech.bytedance.com/api/v3/tts/bidirection",
        app_id: Optional[str] = None,
        access_key: Optional[str] = None,
        config: Optional[TTSConfig] = None,
    ):
        """
        Initialize TTS client.

        Args:
            api_key: API Key for new console authentication
            resource_id: Resource ID (e.g., "seed-tts-2.0")
            endpoint: WebSocket endpoint URL
            app_id: App ID for legacy console (optional)
            access_key: Access Key for legacy console (optional)
            config: TTS configuration
        """
        self.api_key = api_key
        self.resource_id = resource_id
        self.endpoint = endpoint
        self.app_id = app_id
        self.access_key = access_key
        self.config = config or TTSConfig(**DEFAULT_BROWSER_CONFIG)

        # Connection state
        self._ws: Optional[any] = None
        self._connection_id: Optional[str] = None
        self._session_info: Optional[SessionInfo] = None
        self._is_connected = False
        self._session_active = False

        # Event callbacks
        self._on_audio_chunk: Optional[Callable[[bytes, bool, bool], None]] = None
        self._on_sentence_start: Optional[Callable[[str], None]] = None
        self._on_sentence_end: Optional[Callable[[str], None]] = None

        # Async utilities
        self._receive_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def connect(self) -> str:
        """
        Establish WebSocket connection and start connection.

        Returns:
            Connection ID

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package is required. Install: pip install websockets")

        if self._is_connected:
            logger.warning("Already connected")
            return self._connection_id

        # Prepare headers
        headers = {}
        if self.app_id and self.access_key:
            # Legacy authentication
            headers.update({
                "X-Api-App-Id": self.app_id,
                "X-Api-Access-Key": self.access_key,
                "X-Api-Resource-Id": self.resource_id,
            })
        else:
            # New authentication
            headers.update({
                "X-Api-Key": self.api_key,
                "X-Api-Resource-Id": self.resource_id,
            })

        # Generate connection ID
        self._connection_id = str(uuid.uuid4())
        headers["X-Api-Connect-Id"] = self._connection_id

        # Optional: Request usage token return
        headers["X-Control-Require-Usage-Tokens-Return"] = "text_words"

        logger.info(f"Connecting to {self.endpoint} with connection_id={self._connection_id}")

        try:
            # Connect with timeout
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    self.endpoint,
                    additional_headers=headers,
                    ping_interval=None,  # Disable auto-ping
                ),
                timeout=10.0,
            )

            # Start connection
            await self._start_connection()
            self._is_connected = True

            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected: {self._connection_id}")
            return self._connection_id

        except asyncio.TimeoutError:
            raise TimeoutError("Connection timeout")
        except Exception as e:
            raise TTSConnectionError(f"Connection failed: {e}")

    async def _start_connection(self):
        """Send StartConnection and wait for ConnectionStarted."""
        # Send StartConnection
        frame = build_frame(
            message_type=FULL_CLIENT_REQUEST,
            event=START_CONNECTION,
            payload={},
        )
        await self._ws.send(frame)
        logger.debug("Sent StartConnection")

        # Wait for ConnectionStarted or ConnectionFailed
        response = await asyncio.wait_for(
            self._event_queue.get(),
            timeout=10.0,
        )

        if response["event"] == CONNECTION_FAILED:
            error_msg = response.get("payload", {}).get("message", "Connection failed")
            raise TTSConnectionError(error_msg)

        if response["event"] != CONNECTION_STARTED:
            raise ProtocolError(f"Expected ConnectionStarted, got {get_event_name(response['event'])}")

        # Log response header if available
        if hasattr(self._ws, "response_headers"):
            log_id = self._ws.response_headers.get("X-Tt-Logid", "")
            if log_id:
                logger.info(f"X-Tt-Logid: {log_id}")

        logger.debug("ConnectionStarted received")

    async def start_session(self, user_id: Optional[str] = None) -> str:
        """
        Start a new TTS session.

        Args:
            user_id: User ID for session tracking

        Returns:
            Session ID

        Raises:
            SessionError: If session start fails
        """
        async with self._lock:
            if self._session_active:
                raise SessionError("Session already active")

            if not self._is_connected:
                await self.connect()

            session_id = str(uuid.uuid4())

            # Build StartSession payload
            payload = {
                "user": {
                    "uid": user_id or "default_user"
                },
                "req_params": self.config.to_params(),
                # Disable markdown filter for better TTS rendering
                "additions": '{"disable_markdown_filter":true}'
            }

            # Send StartSession
            frame = build_frame(
                message_type=FULL_CLIENT_REQUEST,
                event=START_SESSION,
                payload=payload,
                session_id=session_id,
            )
            await self._ws.send(frame)
            logger.debug(f"Sent StartSession with session_id={session_id}")

            # Wait for SessionStarted or SessionFailed
            response = await asyncio.wait_for(
                self._event_queue.get(),
                timeout=10.0,
            )

            if response["event"] == SESSION_FAILED:
                error_msg = response.get("payload", {}).get("message", "Session failed")
                raise SessionError(error_msg)

            if response["event"] != SESSION_STARTED:
                raise ProtocolError(f"Expected SessionStarted, got {get_event_name(response['event'])}")

            self._session_info = SessionInfo(session_id=session_id, is_active=True)
            self._session_active = True

            logger.debug(f"SessionStarted: {session_id}")
            return session_id

    async def send_text(self, text: str) -> AsyncIterator[bytes]:
        """
        Send text for TTS synthesis.

        Args:
            text: Text to synthesize

        Yields:
            Audio chunks as bytes

        Raises:
            SessionError: If no active session
        """
        if not self._session_active or not self._session_info:
            raise SessionError("No active session")

        if not text or not text.strip():
            return

        # Send TaskRequest
        payload = {
            "req_params": {
                "text": text
            }
        }

        frame = build_frame(
            message_type=FULL_CLIENT_REQUEST,
            event=TASK_REQUEST,
            payload=payload,
            session_id=self._session_info.session_id,
        )
        await self._ws.send(frame)
        logger.debug(f"Sent TaskRequest: {text[:50]}...")

        # Yield audio chunks as they arrive
        while True:
            response = await self._event_queue.get()

            if response["event"] == TTS_SENTENCE_START:
                text = response.get("payload", {}).get("text", "")
                logger.debug(f"Sentence start: {text[:30]}...")
                if self._on_sentence_start:
                    self._on_sentence_start(text)

            elif response["event"] == TTS_SENTENCE_END:
                text = response.get("payload", {}).get("text", "")
                logger.debug(f"Sentence end: {text[:30]}...")
                if self._on_sentence_end:
                    self._on_sentence_end(text)

            elif response["event"] == TTS_RESPONSE:
                audio_data = response.get("audio_data")
                if audio_data:
                    yield audio_data
                    self._session_info.audio_chunks_received += 1

            # Check if synthesis is complete (SessionFinished will be received separately)
            # For now, we'll let the caller decide when to stop receiving

    async def finish_session(self) -> Optional[TTSUsage]:
        """
        Finish the current session and wait for SessionFinished.

        Returns:
            Usage statistics if available

        Raises:
            SessionError: If session finish fails
        """
        async with self._lock:
            if not self._session_active or not self._session_info:
                return None

            # Send FinishSession
            frame = build_frame(
                message_type=FULL_CLIENT_REQUEST,
                event=FINISH_SESSION,
                payload={},
                session_id=self._session_info.session_id,
            )
            await self._ws.send(frame)
            logger.debug("Sent FinishSession")

            # Wait for SessionFinished
            response = await asyncio.wait_for(
                self._event_queue.get(),
                timeout=30.0,
            )

            if response["event"] != SESSION_FINISHED:
                raise ProtocolError(f"Expected SessionFinished, got {get_event_name(response['event'])}")

            # Extract usage if available
            usage = None
            payload = response.get("payload", {})
            if payload:
                text_words = payload.get("usage", {}).get("text_words")
                if text_words:
                    usage = TTSUsage(text_words=text_words)

            self._session_active = False
            self._session_info = None

            logger.debug(f"SessionFinished: usage={usage}")
            return usage

    async def cancel_session(self):
        """Cancel the current session."""
        async with self._lock:
            if not self._session_active or not self._session_info:
                return

            # Send CancelSession
            frame = build_frame(
                message_type=FULL_CLIENT_REQUEST,
                event=CANCEL_SESSION,
                payload={},
                session_id=self._session_info.session_id,
            )
            await self._ws.send(frame)
            logger.debug("Sent CancelSession")

            # Wait for SessionCanceled
            try:
                response = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=10.0,
                )
                if response["event"] != SESSION_CANCELED:
                    logger.warning(f"Expected SessionCanceled, got {get_event_name(response['event'])}")
            except asyncio.TimeoutError:
                logger.warning("CancelSession timeout")

            self._session_active = False
            self._session_info = None

    async def close(self):
        """Close the WebSocket connection."""
        if not self._is_connected:
            return

        # Cancel active session if any
        if self._session_active:
            await self.cancel_session()

        # Send FinishConnection if connected
        if self._ws and self._is_connected:
            try:
                frame = build_frame(
                    message_type=FULL_CLIENT_REQUEST,
                    event=FINISH_CONNECTION,
                    payload={},
                )
                await self._ws.send(frame)
                logger.debug("Sent FinishConnection")

                # Wait for ConnectionFinished (with timeout)
                try:
                    response = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=5.0,
                    )
                    if response["event"] != CONNECTION_FINISHED:
                        logger.warning(f"Expected ConnectionFinished, got {get_event_name(response['event'])}")
                except asyncio.TimeoutError:
                    logger.warning("FinishConnection timeout")
            except Exception as e:
                logger.warning(f"Error sending FinishConnection: {e}")

        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        self._is_connected = False
        self._connection_id = None
        logger.info("Connection closed")

    async def _receive_loop(self):
        """Background task to receive and process incoming frames."""
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    try:
                        frame = parse_frame(message)
                        logger.debug(f"Received: event={get_event_name(frame.event)}, "
                                   f"type={frame.message_type}, "
                                   f"audio_len={len(frame.audio_data) if frame.audio_data else 0}")

                        # Put relevant events in queue
                        if frame.event in [
                            CONNECTION_STARTED, CONNECTION_FAILED, CONNECTION_FINISHED,
                            SESSION_STARTED, SESSION_FAILED, SESSION_FINISHED, SESSION_CANCELED,
                            TTS_SENTENCE_START, TTS_SENTENCE_END, TTS_RESPONSE,
                        ]:
                            await self._event_queue.put({
                                "event": frame.event,
                                "payload": frame.payload,
                                "audio_data": frame.audio_data,
                                "error_code": frame.error_code,
                            })

                        # Handle error frames
                        if frame.message_type == 0b1111:  # ERROR_INFORMATION
                            error_msg = frame.payload.get("message", "Unknown error") if frame.payload else "Unknown error"
                            error_code = frame.error_code or 55000000
                            logger.error(f"TTS Error: code={error_code}, msg={error_msg}")
                            await self._event_queue.put({
                                "event": SESSION_FAILED,
                                "payload": {"message": error_msg},
                                "error_code": error_code,
                            })

                    except ProtocolError as e:
                        logger.error(f"Frame parsing error: {e}")

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            # Put error in queue to wake up any waiting coroutines
            try:
                await self._event_queue.put({
                    "event": CONNECTION_FAILED,
                    "payload": {"message": str(e)},
                })
            except Exception:
                pass

    # Callback setters
    def on_audio_chunk(self, callback: Callable[[bytes, bool, bool], None]):
        """Set callback for audio chunks."""
        self._on_audio_chunk = callback

    def on_sentence_start(self, callback: Callable[[str], None]):
        """Set callback for sentence start."""
        self._on_sentence_start = callback

    def on_sentence_end(self, callback: Callable[[str], None]):
        """Set callback for sentence end."""
        self._on_sentence_end = callback

    # Properties
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def session_active(self) -> bool:
        return self._session_active

    @property
    def connection_id(self) -> Optional[str]:
        return self._connection_id

    @property
    def session_id(self) -> Optional[str]:
        return self._session_info.session_id if self._session_info else None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
