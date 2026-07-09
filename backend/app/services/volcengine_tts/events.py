"""
Volcengine TTS Event Constants

火山引擎豆包双向流式语音合成事件常量定义。

Reference: https://www.volcengine.com/docs/6561/79817
"""

# Connection Events
START_CONNECTION = 1
FINISH_CONNECTION = 2

CONNECTION_STARTED = 50
CONNECTION_FAILED = 51
CONNECTION_FINISHED = 52

# Session Events
START_SESSION = 100
CANCEL_SESSION = 101
FINISH_SESSION = 102

SESSION_STARTED = 150
SESSION_CANCELED = 151
SESSION_FINISHED = 152
SESSION_FAILED = 153

# Task Events
TASK_REQUEST = 200

# TTS Events
TTS_SENTENCE_START = 350
TTS_SENTENCE_END = 351
TTS_RESPONSE = 352


# Event name mapping for logging/debugging
EVENT_NAMES = {
    START_CONNECTION: "StartConnection",
    FINISH_CONNECTION: "FinishConnection",
    CONNECTION_STARTED: "ConnectionStarted",
    CONNECTION_FAILED: "ConnectionFailed",
    CONNECTION_FINISHED: "ConnectionFinished",
    START_SESSION: "StartSession",
    CANCEL_SESSION: "CancelSession",
    FINISH_SESSION: "FinishSession",
    SESSION_STARTED: "SessionStarted",
    SESSION_CANCELED: "SessionCanceled",
    SESSION_FINISHED: "SessionFinished",
    SESSION_FAILED: "SessionFailed",
    TASK_REQUEST: "TaskRequest",
    TTS_SENTENCE_START: "TTSSentenceStart",
    TTS_SENTENCE_END: "TTSSentenceEnd",
    TTS_RESPONSE: "TTSResponse",
}


def get_event_name(event_id: int) -> str:
    """Get human-readable event name from event ID."""
    return EVENT_NAMES.get(event_id, f"Unknown({event_id})")
