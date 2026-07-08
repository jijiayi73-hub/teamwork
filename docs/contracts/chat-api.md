# Chat API 说明

## 范围

本文档记录 Inner Garden Chat 模块当前已经实现并被当前自动化测试覆盖的 API 契约。基础路径统一为 `/api/v1`，所有 Chat 接口都需要 `Authorization: Bearer <access_token>`。

## 端点总览

| 方法 | 路径 | 用途 | 当前验证 |
| --- | --- | --- | --- |
| POST | `/api/v1/chat/messages` | 发送用户消息，并返回 AI assistant 消息 | 200、422、504、502 核心路径已测 |
| GET | `/api/v1/chat/conversations` | 分页列出当前用户对话 | 分页、删除后不可见已测 |
| POST | `/api/v1/chat/conversations` | 显式创建对话 | companion、past_self anchor 校验已测 |
| GET | `/api/v1/chat/conversations/{conversation_id}` | 获取对话元数据 | 用户隔离 404 已测 |
| GET | `/api/v1/chat/conversations/{conversation_id}/messages` | 分页获取对话消息 | 正常列表、404 已测 |
| DELETE | `/api/v1/chat/conversations/{conversation_id}` | 软删除对话 | 用户隔离和删除后列表过滤已测 |

## 通用约定

- 认证：所有接口使用 JWT Bearer Token。
- 用户隔离：后端按当前用户过滤 Conversation、Diary 和 Message，不允许跨用户读取或删除。
- 分页：`page >= 1`，`1 <= page_size <= 100`。
- 成功响应：统一包含 `success: true`、`data`、`message`、`request_id`。
- 错误响应：FastAPI/Pydantic 校验错误返回 422；认证失败返回 401；跨用户访问和不存在资源统一返回 404。
- 测试环境：使用 FakeAIProvider、TimeoutAIProvider、FailedAIProvider，不真实调用 OpenAI。

## POST `/api/v1/chat/messages`

### 请求体

```json
{
  "conversation_id": null,
  "mode": "companion",
  "content": "今天想聊聊我的状态",
  "use_memory": false,
  "anchor_diary_id": null
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_id` | integer or null | 否 | 为空时创建新对话；有值时追加到已有对话 |
| `mode` | `companion` or `past_self` or null | 新对话必填 | 新建对话模式 |
| `content` | string | 是 | 用户消息，长度 1 到 5000 |
| `use_memory` | boolean | 否 | 是否检索日记记忆 |
| `anchor_diary_id` | integer or null | past_self 新对话必填 | past_self 模式绑定的日记 |

### 成功响应

- 状态码：200
- 行为：保存 user message；AI 成功时保存 assistant message；返回对话、两条消息、检索信息、来源和安全检查结果。

### AI 失败响应

| 场景 | 状态码 | 持久化行为 |
| --- | --- | --- |
| AI 超时 | 504 | 保存 user message，不创建伪造 assistant message |
| Provider 错误 | 502 | 保存 user message，不创建伪造 assistant message |
| Rate limit | 429 | 预留错误处理路径 |

## Conversation 接口

### GET `/api/v1/chat/conversations`

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |
| `mode` | `companion` or `past_self` | null | 可选模式过滤 |

返回 `conversations`、`page`、`page_size`、`total`。

### POST `/api/v1/chat/conversations`

请求体：

```json
{
  "mode": "past_self",
  "title": "和过去的自己聊聊",
  "anchor_diary_id": 123
}
```

- `mode=companion` 时 `anchor_diary_id` 可为空。
- `mode=past_self` 时必须提供属于当前用户的 `anchor_diary_id`。
- 成功状态码：201。

### GET `/api/v1/chat/conversations/{conversation_id}`

返回当前用户可访问的对话元数据。不存在、已删除或属于其他用户时返回 404。

### GET `/api/v1/chat/conversations/{conversation_id}/messages`

返回消息历史，assistant 消息可带 `sources`。不存在、已删除或属于其他用户时返回 404。

### DELETE `/api/v1/chat/conversations/{conversation_id}`

软删除当前用户自己的对话，成功返回：

```json
{
  "deleted_conversation_id": 123
}
```

## 当前自动化验证

2026-07-08 运行：

```bash
cd backend
py -m pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_retrieval_service.py tests/test_safety_service.py -v --tb=short
```

结果：21 passed, 3 warnings。

## 当前启动验证

2026-07-08，用户在 `backend` 目录运行：

```bash
py -m uvicorn app.main:app --reload
```

服务启动成功，并访问：

- `GET /health` 返回 200
- `GET /api/v1/health` 返回 200
- `GET /docs` 返回 200
- `GET /openapi.json` 返回 200

用户侧 PowerShell 验证记录：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Start-Process http://127.0.0.1:8000/docs
$api = Invoke-RestMethod http://127.0.0.1:8000/openapi.json
$api.paths.PSObject.Properties.Name | Where-Object { $_ -like "*chat*" }
```

Chat path 输出：

```text
/api/v1/chat/messages
/api/v1/chat/conversations
/api/v1/chat/conversations/{conversation_id}
/api/v1/chat/conversations/{conversation_id}/messages
```

本轮复查：

```bash
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health
```

结果：200，响应体为 `{"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}`。

OpenAPI 中已暴露 Chat path：

- `/api/v1/chat/messages`
- `/api/v1/chat/conversations`
- `/api/v1/chat/conversations/{conversation_id}`
- `/api/v1/chat/conversations/{conversation_id}/messages`

## 尚未验证

- 未进行前端 UI 到后端的端到端测试。
- 已安装 OpenAI-compatible SDK，并完成真实 DeepSeek Provider 调用。
- 已对真实运行服务发起 authenticated Chat 请求，返回 `message_sent`。
