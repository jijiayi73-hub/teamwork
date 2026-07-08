# Chat API Contract

Version: 1.0
Status: FROZEN
Owner: 前端负责人 + 后端负责人
Effective date: 2026-07-08

唯一有效实现依据：
1. backend/app/schemas/chat.py
2. FastAPI /openapi.json
3. 本文件

若三者冲突，以 backend OpenAPI 为准。
任何破坏性修改必须同时获得前端和后端确认。

## Endpoint

Base path: `/api/v1`

| Method | Path | Purpose | Success |
| --- | --- | --- | --- |
| POST | `/chat/messages` | 发送用户消息，并返回 AI assistant 消息 | 200 |
| GET | `/chat/conversations` | 分页列出当前用户的对话 | 200 |
| POST | `/chat/conversations` | 显式创建对话 | 201 |
| GET | `/chat/conversations/{conversation_id}` | 获取单个对话元数据 | 200 |
| GET | `/chat/conversations/{conversation_id}/messages` | 分页获取对话消息 | 200 |
| DELETE | `/chat/conversations/{conversation_id}` | 软删除对话 | 200 |

所有 Chat endpoint 都需要 `Authorization: Bearer <access_token>`。

后端启动后，机器层面的契约真相是：

- `http://localhost:8000/openapi.json`
- `http://localhost:8000/docs`

后端每次修改 Pydantic Schema 后，必须检查 `/openapi.json`。
前端每次接接口前，必须以 `/openapi.json` 校验类型。

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/generated-api.ts
```

## Request

### POST `/api/v1/chat/messages`

```json
{
  "conversation_id": null,
  "mode": "companion",
  "content": "今天感觉很累",
  "use_memory": false,
  "anchor_diary_id": null
}
```

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `conversation_id` | integer or null | No | `null` creates a new conversation; integer continues an existing user-owned conversation |
| `mode` | `"companion"` or `"past_self"` or null | Required for new conversation | Omit or set null when continuing |
| `content` | string | Yes | 1 to 5000 characters |
| `use_memory` | boolean | No | Default is `false` |
| `anchor_diary_id` | integer or null | Required for new `past_self` conversation | Must belong to current user |

### POST `/api/v1/chat/conversations`

```json
{
  "mode": "past_self",
  "title": "和过去的自己聊聊",
  "anchor_diary_id": 42
}
```

`mode="past_self"` requires `anchor_diary_id`.

### GET list endpoints

`GET /api/v1/chat/conversations`: `page`, `page_size`, optional `mode`.

`GET /api/v1/chat/conversations/{conversation_id}/messages`: `page`, `page_size`.

## Response

All success responses use this envelope:

```json
{
  "success": true,
  "data": {},
  "message": "message_sent",
  "request_id": "local"
}
```

### ChatResponse data

```json
{
  "conversation": {
    "id": 12,
    "mode": "companion",
    "title": "今天感觉有些疲惫",
    "anchor_diary_id": null,
    "started_at": "2026-07-08T10:00:00Z",
    "updated_at": "2026-07-08T10:00:02Z",
    "message_count": 2
  },
  "user_message": {
    "id": 31,
    "conversation_id": 12,
    "role": "user",
    "content": "今天感觉很累",
    "created_at": "2026-07-08T10:00:00Z"
  },
  "assistant_message": {
    "id": 32,
    "conversation_id": 12,
    "role": "assistant",
    "content": "听起来你今天消耗了不少精力。",
    "created_at": "2026-07-08T10:00:02Z"
  },
  "retrieval": {
    "used": false,
    "strategy": "none",
    "total_found": 0,
    "used_in_context": 0
  },
  "sources": [],
  "safety": {
    "flagged": false,
    "level": "none",
    "category": null,
    "action": "none"
  }
}
```

`MessageRead.role` is only `"user"` or `"assistant"`; never use `sender` or `"ai"`.
`conversation.user_id` is never returned.
Use `assistant_message.created_at` as the response timestamp; there is no top-level `created_at`.

### ConversationListResponse data

```json
{
  "conversations": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

### MessageListResponse data

```json
{
  "messages": [
    {
      "message": {
        "id": 31,
        "conversation_id": 12,
        "role": "user",
        "content": "今天感觉很累",
        "created_at": "2026-07-08T10:00:00Z"
      },
      "sources": []
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 1
}
```

## Error

| Status | Meaning | Frontend rule |
| --- | --- | --- |
| 401 | token invalid or missing | Clear invalid token and enter login flow |
| 404 | resource not found or not owned by user | Do not reveal whether another user's resource exists |
| 422 | request validation failed | Show input error and keep user input |
| 429 | rate limited | Keep user input and allow retry later |
| 502 | AI provider error | Keep saved user message; do not create fake assistant reply |
| 504 | AI timeout | Keep saved user message; allow retry; do not create fake assistant reply |

Service-level AI errors currently use this envelope:

```json
{
  "success": false,
  "data": null,
  "message": "ai_service_unavailable",
  "request_id": "local",
  "error_code": "INTERNAL_ERROR",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "AI service is temporarily unavailable",
    "details": {
      "provider": "deepseek",
      "provider_error": "Simulated provider error"
    }
  }
}
```

FastAPI/Pydantic validation details must be checked against `/openapi.json` and current runtime response.

## 状态变化

| Scenario | Backend state change | Frontend state change |
| --- | --- | --- |
| New companion message succeeds | Create conversation, user message, assistant message | Save `conversation.id`; append user and assistant bubbles once |
| Existing conversation message succeeds | Reuse `conversation_id`; create user and assistant messages | Keep current conversation; append user and assistant bubbles once |
| New past_self message succeeds | Create conversation with `anchor_diary_id`; create user and assistant messages | Preserve `anchor_diary_id` association |
| 422 | No AI message | Show validation error; do not remove input content |
| 502 | User message may be saved; no assistant message | Keep user message; show service failure |
| 504 | User message may be saved; no assistant message | Keep user message; allow retry |
| 401 | No chat mutation guaranteed | Clear invalid token; enter login flow |
| Request in progress | Pending network request | Disable duplicate send |

## 示例 JSON

Fixed mock fixtures live in `frontend/src/mocks/chat/`:

- `send-message-success.json`
- `validation-error-422.json`
- `ai-provider-error-502.json`
- `ai-timeout-504.json`
- `conversation-list.json`
- `message-list.json`

Mock 规则：Mock 必须从后端真实响应或测试 Fixture 复制，前端不能自行编造。
