# 任务：接入火山引擎豆包双向流式语音合成 API

请先阅读当前仓库结构和已有后端代码，再实现火山引擎豆包语音的 **WebSocket 双向流式 TTS**。

官方目标接口为：

```text
wss://openspeech.bytedance.com/api/v3/tts/bidirection
```

该接口支持文本流式输入、音频流式输出，适合将大模型正在生成的文本直接转换成语音。不要自行对 LLM 输出进行复杂切句或攒句，火山引擎服务端本身会处理碎片文本和长文本。

---

## 一、实现目标

在后端实现一个独立、可测试、可复用的火山引擎 TTS 模块，并通过 FastAPI WebSocket 暴露给前端。

建议目录：

```text
backend/
├── app/
│   ├── api/
│   │   └── tts.py
│   ├── services/
│   │   └── volcengine_tts/
│   │       ├── client.py
│   │       ├── protocol.py
│   │       ├── events.py
│   │       ├── models.py
│   │       └── exceptions.py
│   └── config.py
└── tests/
    ├── test_tts_protocol.py
    └── test_tts_client.py
```

不要把协议编码、FastAPI 路由和业务逻辑全部写进同一个文件。

---

## 二、鉴权配置

优先采用新版控制台的鉴权方式：

```http
X-Api-Key: <API_KEY>
X-Api-Resource-Id: seed-tts-2.0
X-Api-Connect-Id: <每次连接生成的 UUID>
```

环境变量：

```env
VOLCENGINE_TTS_API_KEY=
VOLCENGINE_TTS_RESOURCE_ID=seed-tts-2.0
VOLCENGINE_TTS_SPEAKER=
VOLCENGINE_TTS_ENDPOINT=wss://openspeech.bytedance.com/api/v3/tts/bidirection
```

兼容旧版控制台时，可以支持：

```env
VOLCENGINE_TTS_APP_ID=
VOLCENGINE_TTS_ACCESS_KEY=
```

对应 Header：

```http
X-Api-App-Id: <APP_ID>
X-Api-Access-Key: <ACCESS_KEY>
X-Api-Resource-Id: <RESOURCE_ID>
```

API Key、Access Key 绝对不能发送给浏览器、写入源码或提交到 Git。`X-Api-Resource-Id` 同时决定模型版本和计费方式，例如 `seed-tts-2.0`、`seed-tts-1.0` 和 `seed-tts-1.0-concurr`。

可选添加：

```http
X-Control-Require-Usage-Tokens-Return: text_words
```

这样在 `SessionFinished` 中可以获得计费字符数。握手成功后记录响应 Header `X-Tt-Logid`，方便定位线上问题。

---

## 三、协议实现要求

该 WebSocket 传输的是二进制帧。

每个帧至少包含：

```text
4 字节协议头
可选 Event
可选 Connection ID / Session ID
Payload Size
Payload
```

所有整数必须使用 **大端序 Big Endian**。

固定基础 Header：

```text
Byte 0:
  高 4 位 Protocol Version = 0001
  低 4 位 Header Size = 0001

Byte 1:
  高 4 位 Message Type
  低 4 位 Message Flags

Byte 2:
  高 4 位 Serialization
  低 4 位 Compression

Byte 3:
  Reserved = 00000000
```

主要类型：

```python
FULL_CLIENT_REQUEST = 0b0001
FULL_SERVER_RESPONSE = 0b1001
AUDIO_ONLY_RESPONSE = 0b1011
ERROR_INFORMATION = 0b1111

WITH_EVENT = 0b0100

SERIALIZATION_RAW = 0b0000
SERIALIZATION_JSON = 0b0001

COMPRESSION_NONE = 0b0000
COMPRESSION_GZIP = 0b0001
```

实现统一函数：

```python
build_frame(
    message_type,
    event,
    payload,
    session_id=None,
    serialization="json",
    compression="none",
) -> bytes
```

以及：

```python
parse_frame(data: bytes) -> ParsedFrame
```

解析结果至少包含：

```python
message_type
event
session_id
connection_id
error_code
payload
audio_data
```

禁止在业务代码中散落手写字节偏移。协议细节集中放在 `protocol.py`。

---

## 四、Event 常量

```python
START_CONNECTION = 1
FINISH_CONNECTION = 2

CONNECTION_STARTED = 50
CONNECTION_FAILED = 51
CONNECTION_FINISHED = 52

START_SESSION = 100
CANCEL_SESSION = 101
FINISH_SESSION = 102

SESSION_STARTED = 150
SESSION_CANCELED = 151
SESSION_FINISHED = 152
SESSION_FAILED = 153

TASK_REQUEST = 200

TTS_SENTENCE_START = 350
TTS_SENTENCE_END = 351
TTS_RESPONSE = 352
```

音频数据主要通过 `TTS_RESPONSE = 352` 返回。不要把所有二进制帧都当作音频帧。

---

## 五、连接状态机

严格按照以下流程实现。

### 1. 创建上游 WebSocket

携带鉴权 Header 连接火山引擎。

### 2. StartConnection

发送 Event `1`：

```json
{}
```

等待服务端返回：

```text
ConnectionStarted = 50
```

收到 `ConnectionFailed = 51` 时立即终止并返回明确错误。

### 3. StartSession

每次合成生成新的 UUID 作为 `session_id`，禁止复用。

发送 Event `100`，Payload 示例：

```json
{
  "user": {
    "uid": "current-user-id"
  },
  "req_params": {
    "speaker": "<VOLCENGINE_TTS_SPEAKER>",
    "audio_params": {
      "format": "pcm",
      "sample_rate": 24000,
      "speech_rate": 0,
      "loudness_rate": 0
    },
    "additions": "{\"disable_markdown_filter\":true}"
  }
}
```

等待：

```text
SessionStarted = 150
```

音色、音频格式、采样率、语速和情绪等服务参数在 `StartSession` 阶段设置。

### 4. TaskRequest

每收到一段文本，就发送 Event `200`：

```json
{
  "req_params": {
    "text": "本次新增的文本片段"
  }
}
```

必须使用当前 Session ID。

文本片段可以直接来自 LLM 的流式输出，不要每个字符创建一个新 Session，也不要每句话重新连接。

### 5. 接收音频

持续读取上游帧：

* `350`：一句开始。
* `351`：一句结束。
* `352`：音频二进制数据。
* `153`：Session 失败。
* 错误帧：解析错误码和错误 Payload。

收到音频后立即转发给前端，不要等整段音频全部生成完成。

### 6. FinishSession

确定没有更多文本后，立即发送 Event `102`：

```json
{}
```

必须继续接收剩余音频，并等待：

```text
SessionFinished = 152
```

在收到 `SessionFinished` 前，不得启动下一轮 Session。

### 7. 复用或关闭连接

同一条 WebSocket 连接可以依次运行多个 Session，但不能同时运行多个 Session。

仍有下一次合成任务时：

```text
重新 StartSession
```

彻底不再使用时：

```text
发送 FinishConnection = 2
等待 ConnectionFinished = 52
关闭 WebSocket
```

官方推荐复用连接，以减少重复握手产生的延迟。

---

## 六、音频参数

基础参数支持：

```json
{
  "format": "pcm",
  "sample_rate": 24000,
  "speech_rate": 0,
  "loudness_rate": 0
}
```

支持的格式包括：

```text
mp3
ogg_opus
pcm
```

采样率支持：

```text
8000
16000
22050
24000
32000
44100
48000
```

实时浏览器播放优先使用：

```text
pcm + 24000 Hz
```

原因是流式 WAV 可能重复返回 WAV Header；使用 PCM 更适合连续播放。如果使用 MP3 或 OGG，应主动设置合理的 `bit_rate`，不要无脑依赖默认值。

可选参数：

```json
{
  "emotion": "happy",
  "emotion_scale": 4,
  "speech_rate": 0,
  "loudness_rate": 0,
  "enable_subtitle": false,
  "enable_timestamp": false
}
```

只有部分音色支持 emotion，代码中不要默认认为全部音色支持。

---

## 七、FastAPI 对外接口

实现：

```text
WebSocket /api/tts/stream
```

浏览器与后端之间使用简单 JSON 控制消息和二进制音频消息。

前端发送：

```json
{
  "type": "start",
  "speaker": "可选音色",
  "format": "pcm",
  "sample_rate": 24000
}
```

流式发送文本：

```json
{
  "type": "text",
  "text": "你好，这是第一段文本。"
}
```

结束文本输入：

```json
{
  "type": "finish"
}
```

取消：

```json
{
  "type": "cancel"
}
```

后端发送控制事件：

```json
{
  "type": "session_started",
  "session_id": "..."
}
```

```json
{
  "type": "sentence_start",
  "text": "..."
}
```

```json
{
  "type": "sentence_end",
  "text": "..."
}
```

```json
{
  "type": "finished",
  "usage": {
    "text_words": 20
  }
}
```

音频必须以 WebSocket binary message 直接发送，不要先 Base64 编码，避免增加约三分之一的数据体积。

---

## 八、异常处理

至少处理：

```text
HTTP/WebSocket 握手失败
鉴权失败
ConnectionFailed
SessionFailed
错误二进制帧
非法协议帧
Payload 长度不一致
JSON 解码失败
上游连接超时
前端主动断开
前端取消 Session
Session 未结束时重复 Start
连接中同时创建多个 Session
```

官方基础错误码：

```python
20000000  # 成功
45000000  # 客户端通用错误
45000001  # 请求参数错误
55000000  # 服务端通用错误
55000001  # 服务端 Session 错误
```

不要只返回“语音生成失败”。错误日志至少包含：

```text
X-Tt-Logid
connection_id
session_id
event
error_code
服务端 message
```

但日志不得打印 API Key、Access Key 或完整鉴权 Header。

---

## 九、并发和资源清理

使用 `asyncio` 实现读写并发：

```text
任务 A：接收前端文本并发送给火山引擎
任务 B：接收火山引擎音频并转发前端
```

需要：

```python
asyncio.Queue
asyncio.TaskGroup
asyncio.Lock
asyncio.Event
```

一条上游连接同一时间只允许一个 Session。

任何异常退出都必须：

1. 尝试发送 CancelSession。
2. 取消读写任务。
3. 关闭上游 WebSocket。
4. 关闭前端 WebSocket。
5. 清理队列和 Session 状态。

不得出现后台 Task 泄漏。

---

## 十、测试要求

### 单元测试

测试：

```text
基础 Header 编码
Event 大端序编码
Session ID 长度和内容
JSON Payload 编码
音频帧解析
错误帧解析
非法长度检测
gzip Payload 解压
```

### Mock 集成测试

模拟服务端依次返回：

```text
ConnectionStarted
SessionStarted
TTSSentenceStart
多个 TTSResponse 音频帧
TTSSentenceEnd
SessionFinished
```

验证：

```text
所有音频分片均按顺序转发
FinishSession 后仍继续接收剩余音频
必须收到 SessionFinished 才结束
异常时资源被正确关闭
```

### 可选真实测试

只有存在完整环境变量时才运行真实 API 测试，否则自动跳过。

---

## 十一、交付要求

完成后输出：

1. 修改和新增的文件列表。
2. 完整调用流程说明。
3. 环境变量配置示例。
4. FastAPI 启动方式。
5. 前端测试 WebSocket 的示例代码。
6. curl 无法测试 WebSocket 时，提供 Python 测试脚本。
7. 单元测试执行结果。
8. 尚未验证或存在风险的部分。

不要伪造成功结果。没有真实 API Key 时，只能声明 Mock 测试通过，不能声称真实火山引擎调用通过。

实现前先检查项目现有依赖、配置方式和路由风格，优先复用现有结构。不要修改无关业务代码，不要改变现有 React 页面视觉效果。
