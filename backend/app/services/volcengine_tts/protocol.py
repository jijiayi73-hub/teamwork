"""
Volcengine TTS Protocol Implementation

火山引擎豆包双向流式语音合成协议编解码。

Protocol Reference:
https://www.volcengine.com/docs/6561/79817

Frame Structure:
┌──────────────────────────────────────────────────────────────┐
│ 4-byte Protocol Header                                       │
├───────────┬───────────┬───────────────┬──────────────────────┤
│ Byte 0   │ Byte 1    │ Byte 2        │ Byte 3               │
├───────────┼───────────┼───────────────┼──────────────────────┤
│ Protocol │ Message   │ Serialization │ Reserved = 00000000   │
│ Version  │ Type/Flag │ Compression   │                      │
│ (0001)   │           │               │                      │
└───────────┴───────────┴───────────────┴──────────────────────┘
│ Optional Event (Variable Big Endian)                          │
│ Optional Connection ID / Session ID (16 bytes)               │
│ Payload Size (4 bytes, Big Endian)                           │
│ Payload (JSON or binary audio data)                          │
└──────────────────────────────────────────────────────────────┘

All integers use Big Endian byte order.
"""

import struct
import gzip
import json
from dataclasses import dataclass
from typing import Optional, Literal
from .events import get_event_name
from .exceptions import ProtocolError


# Protocol Constants
PROTOCOL_VERSION = 0b0001
HEADER_SIZE = 0b0001

# Message Types (Byte 1, high 4 bits)
FULL_CLIENT_REQUEST = 0b0001
FULL_SERVER_RESPONSE = 0b1001
AUDIO_ONLY_RESPONSE = 0b1011
ERROR_INFORMATION = 0b1111

# Message Flags (Byte 1, low 4 bits)
WITH_EVENT = 0b0100

# Serialization (Byte 2, high 4 bits)
SERIALIZATION_RAW = 0b0000
SERIALIZATION_JSON = 0b0001

# Compression (Byte 2, low 4 bits)
COMPRESSION_NONE = 0b0000
COMPRESSION_GZIP = 0b0001

# Reserved (Byte 3)
RESERVED = 0b00000000


@dataclass
class ParsedFrame:
    """Parsed WebSocket frame."""
    message_type: int
    event: Optional[int] = None
    session_id: Optional[str] = None
    connection_id: Optional[str] = None
    error_code: Optional[int] = None
    payload: Optional[dict] = None
    audio_data: Optional[bytes] = None
    serialization: str = "json"
    compression: str = "none"


def build_frame(
    message_type: int,
    event: Optional[int] = None,
    payload: Optional[str | dict | bytes] = None,
    session_id: Optional[str] = None,
    serialization: Literal["raw", "json"] = "json",
    compression: Literal["none", "gzip"] = "none",
) -> bytes:
    """
    Build a Volcengine TTS protocol frame.

    Protocol Format:
    - Header (4 bytes)
    - Event Type (4 bytes, big-endian int) - only if event is provided
    - Session ID Length (4 bytes, big-endian int) + Session ID bytes - only if session_id is provided
    - Payload Length (4 bytes, big-endian int)
    - Payload bytes

    Args:
        message_type: Message type (FULL_CLIENT_REQUEST, etc.)
        event: Event ID (optional, required for most requests) - encoded as 4-byte big-endian int
        payload: Payload data (dict for JSON, bytes for binary)
        session_id: Session ID string (optional, required for START_SESSION and TASK_REQUEST)
        serialization: Serialization method ("json" or "raw")
        compression: Compression method ("none" or "gzip")

    Returns:
        Complete frame as bytes
    """
    # Build Byte 0: Protocol Version (high) + Header Size (low)
    byte0 = (PROTOCOL_VERSION << 4) | HEADER_SIZE

    # Build Byte 1: Message Type (high) + Flags (low)
    byte1_high = message_type << 4
    byte1_low = WITH_EVENT if event is not None else 0b0000
    byte1 = byte1_high | byte1_low

    # Build Byte 2: Serialization (high) + Compression (low)
    byte2_high = SERIALIZATION_JSON if serialization == "json" else SERIALIZATION_RAW
    byte2_low = COMPRESSION_GZIP if compression == "gzip" else COMPRESSION_NONE
    byte2 = (byte2_high << 4) | byte2_low

    # Byte 3: Reserved
    byte3 = RESERVED

    # Build frame as bytearray for easier appending
    frame = bytearray()
    frame.extend([byte0, byte1, byte2, byte3])

    # Add event type if present (4-byte big-endian int)
    if event is not None:
        frame.extend(struct.pack('>I', event))

    # Add session ID if present (4-byte length + UTF-8 bytes)
    if session_id:
        session_id_bytes = session_id.encode('utf-8')
        frame.extend(struct.pack('>I', len(session_id_bytes)))
        frame.extend(session_id_bytes)

    # Prepare payload bytes
    payload_bytes = b''

    if payload is not None:
        if isinstance(payload, dict):
            payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        elif isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        elif isinstance(payload, bytes):
            payload_bytes = payload
        else:
            raise ProtocolError(f"Unsupported payload type: {type(payload)}")

        # Apply compression
        if compression == "gzip":
            payload_bytes = gzip.compress(payload_bytes)

    # Add payload size (4 bytes big-endian)
    frame.extend(struct.pack('>I', len(payload_bytes)))

    # Add payload
    frame.extend(payload_bytes)

    return bytes(frame)


def parse_frame(data: bytes) -> ParsedFrame:
    """
    Parse a Volcengine TTS protocol frame.

    Protocol Format:
    - Header (4 bytes)
    - Event Type (4 bytes, big-endian int) - if has_event flag is set
    - Session ID Length (4 bytes) + Session ID bytes - if present
    - Payload Length (4 bytes, big-endian int)
    - Payload bytes

    Note: Server error responses (flags=0) have a different format:
    - Header (4 bytes)
    - Unknown 4 bytes (possibly error code or metadata)
    - Payload Length (4 bytes, big-endian int)
    - Payload bytes

    Args:
        data: Raw frame bytes

    Returns:
        ParsedFrame object with parsed data

    Raises:
        ProtocolError: If frame is invalid or cannot be parsed
    """
    if len(data) < 4:
        raise ProtocolError(f"Frame too short: {len(data)} bytes, minimum 4 bytes")

    # Parse 4-byte header
    byte0, byte1, byte2, byte3 = struct.unpack('BBBB', data[:4])

    # Extract header fields
    protocol_version = (byte0 >> 4) & 0x0F
    header_size = (byte0 & 0x0F) * 4  # Header size is in 4-byte units
    message_type = (byte1 >> 4) & 0x0F
    has_event = (byte1 & 0x0F) == WITH_EVENT
    serialization = (byte2 >> 4) & 0x0F
    compression = byte2 & 0x0F

    offset = 4

    # Parse event type if present (4-byte big-endian int)
    event = None
    if has_event:
        if offset + 4 > len(data):
            raise ProtocolError("Frame too short to read event type")
        event = struct.unpack('>I', data[offset:offset + 4])[0]
        offset += 4
    elif message_type == ERROR_INFORMATION:
        # Server error responses have an extra 4-byte field before payload_size
        # Skip this unknown field (possibly error code or metadata)
        offset += 4

    # Parse session ID if present
    # Session ID is only present in certain request/response types with event
    # (e.g., START_SESSION, TASK_REQUEST, SESSION_STARTED, etc.)
    session_id = None
    # Only try to parse session_id if we have an event (flags indicate extended format)
    # AND the message type is one that typically carries session_id
    if has_event and message_type in (FULL_CLIENT_REQUEST, FULL_SERVER_RESPONSE):
        if offset + 4 <= len(data):
            # Peek at session_id_len to see if it's reasonable
            potential_session_id_len = struct.unpack('>I', data[offset:offset + 4])[0]
            # Check if this looks like a valid session_id_len (not too large)
            # and if there's enough data for it + payload_len (4 bytes)
            if 0 < potential_session_id_len < 256:
                if offset + 4 + potential_session_id_len + 4 <= len(data):
                    session_id_bytes = data[offset + 4:offset + 4 + potential_session_id_len]
                    try:
                        session_id = session_id_bytes.decode('utf-8')
                        offset += 4 + potential_session_id_len
                    except UnicodeDecodeError:
                        # Not valid UTF-8, skip session_id parsing
                        pass

    # Parse payload size (4 bytes big-endian)
    if offset + 4 > len(data):
        raise ProtocolError("Frame too short to read payload size")

    payload_size = struct.unpack('>I', data[offset:offset + 4])[0]
    offset += 4

    # Parse payload
    if offset + payload_size > len(data):
        raise ProtocolError(
            f"Frame too short for payload: expected {payload_size} bytes, "
            f"got {len(data) - offset} bytes"
        )

    payload_bytes = data[offset:offset + payload_size]

    # Decompress if needed
    if compression == COMPRESSION_GZIP:
        try:
            payload_bytes = gzip.decompress(payload_bytes)
        except Exception as e:
            raise ProtocolError(f"Failed to decompress payload: {e}")

    # Parse payload based on message type and serialization
    parsed_payload = None
    audio_data = None
    error_code = None

    if message_type == AUDIO_ONLY_RESPONSE:
        # Binary audio data
        audio_data = payload_bytes
    elif serialization == SERIALIZATION_JSON and payload_bytes:
        try:
            parsed_payload = json.loads(payload_bytes.decode('utf-8'))
            # Check for error code in payload
            if isinstance(parsed_payload, dict):
                error_code = parsed_payload.get('code')
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ProtocolError(f"Failed to decode JSON payload: {e}")
    elif payload_bytes:
        # Raw string payload
        parsed_payload = {'raw': payload_bytes.decode('utf-8', errors='replace')}

    return ParsedFrame(
        message_type=message_type,
        event=event,
        session_id=session_id,
        error_code=error_code,
        payload=parsed_payload,
        audio_data=audio_data,
        serialization="json" if serialization == SERIALIZATION_JSON else "raw",
        compression="gzip" if compression == COMPRESSION_GZIP else "none",
    )


# Variable int encoding functions are no longer needed
# The protocol uses fixed 4-byte big-endian integers for event type
# Kept for reference in case future protocol versions need them
# def encode_variable_int(value: int) -> bytes:
#     ...
# def decode_variable_int(data: bytes) -> tuple[int, int]:
#     ...
