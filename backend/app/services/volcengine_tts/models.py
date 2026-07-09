"""
Volcengine TTS Data Models

TTS功能的数据模型定义。
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum


class AudioFormat(str, Enum):
    """支持的音频格式"""
    MP3 = "mp3"
    OGG_OPUS = "ogg_opus"
    PCM = "pcm"


class SampleRate(int, Enum):
    """支持的采样率"""
    RATE_8000 = 8000
    RATE_16000 = 16000
    RATE_22050 = 22050
    RATE_24000 = 24000
    RATE_32000 = 32000
    RATE_44100 = 44100
    RATE_48000 = 48000


# 推荐用于实时浏览器播放的配置
DEFAULT_BROWSER_CONFIG = {
    "format": AudioFormat.PCM,
    "sample_rate": SampleRate.RATE_24000,
}


@dataclass
class TTSConfig:
    """TTS配置参数"""
    speaker: str = "zh_female_qingxin"
    format: AudioFormat = AudioFormat.PCM
    sample_rate: int = SampleRate.RATE_24000.value
    speech_rate: float = 0.0  # 语速调整，范围 [-1.0, 1.0]
    loudness_rate: float = 0.0  # 音量调整，范围 [-1.0, 1.0]
    emotion: Optional[str] = None  # 情绪 (仅部分音色支持)
    emotion_scale: int = 0  # 情绪强度，范围 [0, 10]
    enable_subtitle: bool = False
    enable_timestamp: bool = False

    def to_params(self) -> dict:
        """转换为API请求参数"""
        params = {
            "speaker": self.speaker,
            "audio_params": {
                "format": self.format.value,
                "sample_rate": self.sample_rate,
                "speech_rate": self.speech_rate,
                "loudness_rate": self.loudness_rate,
            }
        }

        # 添加可选参数
        if self.emotion:
            params["emotion"] = self.emotion
        if self.emotion_scale > 0:
            params["emotion_scale"] = self.emotion_scale
        if self.enable_subtitle:
            params["enable_subtitle"] = True
        if self.enable_timestamp:
            params["enable_timestamp"] = True

        return params


@dataclass
class TTSRequest:
    """TTS请求"""
    text: str
    config: TTSConfig = field(default_factory=TTSConfig)
    session_id: Optional[str] = None

    def to_task_request(self) -> dict:
        """转换为Task Request payload"""
        return {
            "req_params": {
                "text": self.text,
                **self.config.to_params()
            }
        }


@dataclass
class TTSResponse:
    """TTS音频响应"""
    audio_data: bytes
    format: AudioFormat
    sample_rate: int
    is_end: bool = False
    text: Optional[str] = None


@dataclass
class TTSChunk:
    """TTS音频分片"""
    data: bytes
    is_first: bool = False
    is_last: bool = False
    text: Optional[str] = None


@dataclass
class SessionInfo:
    """TTS会话信息"""
    session_id: str
    connection_id: Optional[str] = None
    is_active: bool = True
    total_text_length: int = 0
    audio_chunks_received: int = 0


@dataclass
class TTSUsage:
    """TTS使用统计"""
    text_words: int  # 计费字符数


# 常用音色列表 (参考火山引擎文档)
POPULAR_SPEAKERS = {
    "zh_female_qingxin": "女声-清新",
    "zh_female_wanxiaomei": "女声-婉小妹",
    "zh_male_zhiboshenquan": "男声-之博深情",
    "zh_male_zhiboyangguang": "男声-之博阳光",
    "zh_female_qiaoke": "女声-可可",
    "zh_male_wukong": "男声-悟空",
}
