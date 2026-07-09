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

    Args:
        message_type: Message type (FULL_CLIENT_REQUEST, etc.)
        event: Event ID (optional, required for most requests)
        payload: Payload data (dict for JSON, bytes for binary)
        session_id: Session ID (16 bytes UUID, optional)
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
    byte2 = byte2_high | byte2_low

    # Byte 3: Reserved
    byte3 = RESERVED

    # Build frame parts
    frame_parts = []

    # Add 4-byte header
    header = bytes([byte0, byte1, byte2, byte3])
    frame_parts.append(header)

    # Add event if present (variable-length big-endian)
    if event is not None:
        # Encode event as variable big-endian bytes
        event_bytes = encode_variable_int(event)
        frame_parts.append(event_bytes)

    # Add session ID if present (16 bytes)
    if session_id:
        import uuid
        try:
            session_uuid = uuid.UUID(session_id)
            session_bytes = session_uuid.bytes
        except (ValueError, AttributeError):
            # If not a valid UUID, use string bytes padded/truncated to 16
            session_bytes = session_id.encode('utf-8')[:16].ljust(16, b'\x00')
        frame_parts.append(session_bytes)

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
    payload_size_bytes = struct.pack('>I', len(payload_bytes))
    frame_parts.append(payload_size_bytes)

    # Add payload
    frame_parts.append(payload_bytes)

    # Combine all parts
    return b''.join(frame_parts)


def parse_frame(data: bytes) -> ParsedFrame:
    """
    Parse a Volcengine TTS protocol frame.

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
    header_size = byte0 & 0x0F
    message_type = (byte1 >> 4) & 0x0F
    has_event = (byte1 & 0x0F) == WITH_EVENT
    serialization = (byte2 >> 4) & 0x0F
    compression = byte2 & 0x0F

    offset = 4

    # Parse event if present
    event = None
    if has_event:
        event, event_length = decode_variable_int(data[offset:])
        offset += event_length

    # Parse session ID if present (16 bytes after event)
    # The protocol may include session ID in some responses
    session_id = None
    if offset + 16 <= len(data):
        # Check if this looks like a UUID (not empty/nulls)
        potential_uuid = data[offset:offset + 16]
        if any(b != 0 for b in potential_uuid):
            import uuid
            try:
                session_uuid = uuid.UUID(bytes=potential_uuid)
                session_id = str(session_uuid)
                offset += 16
            except ValueError:
                # Not a valid UUID, don't advance offset
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


def encode_variable_int(value: int) -> bytes:
    """
    Encode integer as variable-length big-endian bytes.
    Similar to Protocol Buffers varint encoding.
    """
    if value < 0:
        raise ProtocolError(f"Cannot encode negative integer: {value}")

    if value == 0:
        return b'\x00'

    bytes_list = []
    while value > 0:
        # Take lowest 7 bits, set continuation bit if more bytes follow
        byte = value & 0x7F
        value >>= 7
        if value > 0:
            byte |= 0x80  # Set continuation bit
        bytes_list.append(byte)

    return bytes(bytes_list)


def decode_variable_int(data: bytes) -> tuple[int, int]:
    """
    Decode variable-length big-endian integer.

    Returns:
        Tuple of (decoded_value, bytes_consumed)
    """
    value = 0
    shift = 0
    bytes_consumed = 0

    for byte in data:
        bytes_consumed += 1
        # Take lower 7 bits
        value |= (byte & 0x7F) << shift
        # Check continuation bit
        if not (byte & 0x80):
            break
        shift += 7
        # Safety limit (prevent infinite loop on malformed data)
        if shift > 28:  # 4 bytes max for reasonable values
            raise ProtocolError("Variable integer too long")

    return value, bytes_consumed
