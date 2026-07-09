#!/usr/bin/env python3
"""Full TTS test - send text and receive audio."""
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
from app.services.volcengine_tts.events import (
    START_CONNECTION, CONNECTION_STARTED, CONNECTION_FAILED,
    START_SESSION, SESSION_STARTED, SESSION_FAILED,
    TASK_REQUEST, TTS_SENTENCE_START, TTS_SENTENCE_END, TTS_RESPONSE,
    FINISH_SESSION, SESSION_FINISHED,
    get_event_name
)

api_key = os.getenv('VOLCENGINE_TTS_API_KEY')
connection_id = str(uuid.uuid4())

headers = {
    'X-Api-Key': api_key,
    'X-Api-Resource-Id': 'seed-tts-2.0',
    'X-Api-Connect-Id': connection_id
}

uri = 'wss://openspeech.bytedance.com/api/v3/tts/bidirection'

async def test():
    try:
        ws = await websockets.connect(uri, additional_headers=headers, ping_interval=None)
        print(f"Connected: {connection_id}")

        # 1. Send START_CONNECTION
        frame = build_frame(FULL_CLIENT_REQUEST, START_CONNECTION, {})
        print(f"Sending START_CONNECTION: {binascii.hexlify(frame).decode()}")
        await ws.send(frame)

        response = await asyncio.wait_for(ws.recv(), timeout=5)
        parsed = parse_frame(response)
        print(f"Response: {get_event_name(parsed.event) if parsed.event else 'No event'}")
        if parsed.event == CONNECTION_FAILED:
            print(f"Connection failed: {parsed.payload}")
            return

        # 2. Send START_SESSION
        session_id = str(uuid.uuid4())
        payload = {
            "user": {"uid": "test_user"},
            "req_params": {
                # Use a speaker compatible with seed-tts-2.0
                "speaker": "zh_moon_moon",
                "audio_params": {"format": "mp3", "sample_rate": 24000},
                "speed": 1.0,
                "volume": 1.0,
            },
            "additions": '{"disable_markdown_filter":true}'
        }
        frame = build_frame(FULL_CLIENT_REQUEST, START_SESSION, payload, session_id)
        print(f"\nSending START_SESSION with session_id={session_id}")
        await ws.send(frame)

        response = await asyncio.wait_for(ws.recv(), timeout=5)
        parsed = parse_frame(response)
        print(f"Response: {get_event_name(parsed.event) if parsed.event else 'No event'}")
        if parsed.event == SESSION_FAILED:
            print(f"Session failed: {parsed.payload}")
            return

        # 3. Send TASK_REQUEST with text
        text = "你好，这是一个测试"
        payload = {
            "event": TASK_REQUEST,
            "req_params": {"text": text}
        }
        frame = build_frame(FULL_CLIENT_REQUEST, TASK_REQUEST, payload, session_id)
        print(f"\nSending TASK_REQUEST with text: {text}")
        await ws.send(frame)

        # Receive audio chunks
        audio_received = 0
        sentence_count = 0
        max_loops = 20  # Prevent infinite loop
        loop_count = 0
        while loop_count < max_loops:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                parsed = parse_frame(response)
                event = parsed.event
                event_name = get_event_name(event) if event else 'No event'

                print(f"  Received: {event_name} (msg_type={parsed.message_type})")
                if parsed.payload:
                    print(f"    Payload: {parsed.payload}")

                if event == TTS_SENTENCE_START:
                    sentence_count += 1
                    print(f"  Sentence {sentence_count} started")
                elif event == TTS_SENTENCE_END:
                    print(f"  Sentence {sentence_count} ended")
                elif event == TTS_RESPONSE:
                    audio_data = parsed.audio_data
                    if audio_data:
                        audio_received += len(audio_data)
                        print(f"  Audio chunk: {len(audio_data)} bytes (total: {audio_received})")
                elif event == SESSION_FINISHED:
                    print(f"\nSession finished")
                    break
                loop_count += 1
            except asyncio.TimeoutError:
                print("\nTimeout waiting for more data")
                break

        # 4. Send FINISH_SESSION
        frame = build_frame(FULL_CLIENT_REQUEST, FINISH_SESSION, {}, session_id)
        print(f"Sending FINISH_SESSION")
        await ws.send(frame)

        await ws.close()
        print(f"\nTest completed! Received {audio_received} bytes of audio")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
