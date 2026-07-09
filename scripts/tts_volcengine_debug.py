#!/usr/bin/env python3
"""Debug script for Volcengine TTS connection."""
import asyncio
import uuid
import websockets
import os
import sys
import binascii
import struct
import json

sys.path.insert(0, '/app')
from app.services.volcengine_tts.protocol import build_frame, parse_frame, FULL_CLIENT_REQUEST
from app.services.volcengine_tts.events import START_CONNECTION, CONNECTION_STARTED, CONNECTION_FAILED

api_key = os.getenv('VOLCENGINE_TTS_API_KEY')
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key prefix: {api_key[:10]}...")

connection_id = str(uuid.uuid4())
print(f"Connection ID: {connection_id}")

headers = {
    'X-Api-Key': api_key,
    'X-Api-Resource-Id': 'seed-tts-2.0',
    'X-Api-Connect-Id': connection_id
}

uri = 'wss://openspeech.bytedance.com/api/v3/tts/bidirection'
print(f"Connecting to: {uri}")

async def test():
    try:
        ws = await websockets.connect(uri, additional_headers=headers, ping_interval=None)

        # Build frame
        frame = build_frame(FULL_CLIENT_REQUEST, START_CONNECTION, {})
        print(f"Sending frame ({len(frame)} bytes): {binascii.hexlify(frame).decode()}")

        # Parse our sent frame for debugging
        byte0, byte1, byte2, byte3 = struct.unpack('BBBB', frame[:4])
        print(f"Sent header: {byte0:02x} {byte1:02x} {byte2:02x} {byte3:02x}")
        print(f"  Protocol version: {(byte0 >> 4) & 0x0F}")
        print(f"  Header size: {byte0 & 0x0F}")
        print(f"  Message type: {(byte1 >> 4) & 0x0F}")
        print(f"  Has event: {(byte1 & 0x0F) == 0b0100}")

        # Parse event type (4 bytes)
        if len(frame) >= 8:
            event_type = struct.unpack('>I', frame[4:8])[0]
            print(f"  Event type: {event_type} (START_CONNECTION={START_CONNECTION})")

        await ws.send(frame)

        # Wait for response
        response = await asyncio.wait_for(ws.recv(), timeout=5)

        if isinstance(response, bytes):
            hex_str = binascii.hexlify(response).decode()
            print(f"\nResponse length: {len(response)} bytes")
            print(f"Response hex: {hex_str}")

            # Parse using our parser
            parsed = parse_frame(response)
            print(f"\nParsed frame:")
            print(f"  Message type: {parsed.message_type}")
            print(f"  Event: {parsed.event}")
            print(f"  Session ID: {parsed.session_id}")
            print(f"  Payload: {parsed.payload}")

            # Try to extract JSON error message
            json_start = response.find(b'{')
            if json_start >= 0:
                json_part = response[json_start:]
                error_msg = json_part.decode('utf-8', errors='ignore')
                print(f"\nJSON payload: {error_msg}")

                # Try to parse as JSON
                try:
                    parsed_json = json.loads(error_msg)
                    print(f"Parsed error: {json.dumps(parsed_json, indent=2, ensure_ascii=False)}")
                except:
                    pass

            # Check if connection succeeded
            if parsed.event == CONNECTION_STARTED:
                print(f"\nSUCCESS: Connection established!")
            elif parsed.event == CONNECTION_FAILED:
                print(f"\nFAILED: Connection failed")
        else:
            print(f"Response (str): {response}")

        await ws.close()

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
