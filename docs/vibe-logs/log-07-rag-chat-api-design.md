# Inner Garden Chat API Design Document

## Version: 1.2.1 (Historical Sources Support)
## Date: 2026-07-08
## Status: Design Phase - Database Schema Fixed

## Changelog
- v1.2.1: Added historical message sources support - ChatHistoryItem now includes sources for assistant messages, separate from MessageRead to avoid circular dependencies
- v1.2: API Contract Freeze - Fixed status code strategy (Pydantic validators return 422), unified AI failure handling (return 502/504 not success=true), standardized field naming (mode/role/assistant), removed user_id from responses, simplified source_type, removed hardcoded contact numbers
- v1.1: Applied design review feedback - sources deduplication, 422/400 clarification, mode/anchor only for new conversations, structured safety enums, unified 404 strategy
- v1.0: Initial design

---

# A. Why Use a Unified Chat Interface?

## Design Rationale

### 1. Shared Domain Model

Both AI Companion Chat and Past Self Chat share fundamental concepts:
- **Conversation**: A chat session between user and AI
- **Messages**: Turn-based exchange of user inputs and AI responses
- **Context Retrieval**: Fetching relevant historical diaries
- **AI Generation**: Calling LLM with structured prompts
- **User Isolation**: All data scoped to current user

The only differences are:
- **Conversation mode**: companion vs past_self
- **Retrieval scope**: optional vs required (with anchor diary)
- **Prompt template**: different system instructions
- **Tone**: gentle companion vs reflective past self

### 2. Code Reusability

Unified interface enables:
- Single `Conversation` and `Message` model
- Single `chat_service.py` for business logic
- Single `retrieval_service.py` for diary fetching
- Single `ai_provider.py` for LLM calls
- Shared frontend components (`ChatWindow`, `MessageBubble`)

### 3. Consistent User Experience

Users perceive "chat with AI" as one feature, not two:
- Same UI patterns
- Same message history behavior
- Same loading/error states
- Different modes are just contextual variations

### 4. Simplified Testing

Unified interface reduces test surface:
- One set of conversation CRUD tests
- One set of message storage tests
- Mode-specific tests as variations, not separate suites

### 5. Future Extensibility

Adding new chat modes becomes trivial:
- Just add new `mode` value
- Add prompt template
- Add retrieval strategy
- No new endpoints needed

### 6. RESTful Alignment

```
/chat/conversations     - Collection of conversations
/chat/conversations/{id} - Specific conversation
/chat/conversations/{id}/messages - Messages in conversation
/chat/messages          - Send message (creates or continues conversation)
```

This follows REST principle of treating conversations as resources with messages as sub-resources.

---

# B. Interface List Table

| HTTP Method | URL | Purpose | Auth | Request Parameters | Response Fields | Status Codes |
|-------------|-----|---------|------|-------------------|-----------------|--------------|
| **POST** | `/api/v1/chat/messages` | Send message, get AI response, auto-create conversation if needed | Required | See section C | See section D | 200, 400, 401, 404, 422, 429, 502, 504 |
| **GET** | `/api/v1/chat/conversations` | List user's conversations | Required | `page?`, `page_size?`, `mode?` | `conversations`, `pagination`, `total` | 200, 401, 422 |
| **POST** | `/api/v1/chat/conversations` | Create new conversation explicitly | Required | `mode`, `title?`, `anchor_diary_id?` | `conversation`, `created_at` | 201, 400, 401, 422 |
| **GET** | `/api/v1/chat/conversations/{conversation_id}` | Get conversation metadata | Required | - | `conversation` | 200, 401, 404 |
| **GET** | `/api/v1/chat/conversations/{conversation_id}/messages` | Get messages in conversation | Required | `page?`, `page_size?` | `messages`, `pagination`, `total` | 200, 401, 404, 422 |
| **DELETE** | `/api/v1/chat/conversations/{conversation_id}` | Delete conversation (soft delete) | Required | - | `deleted_conversation_id` | 200, 401, 404 |

### Endpoint Details

#### POST /api/v1/chat/messages
**Primary endpoint for sending messages.** Auto-creates conversation if `conversation_id` not provided.

#### GET /api/v1/chat/conversations
**List conversations** with optional mode filtering. Supports pagination.

#### POST /api/v1/chat/conversations
**Explicit conversation creation.** Useful for pre-creating conversations (e.g., when clicking "Start Chat" button).

#### GET /api/v1/chat/conversations/{conversation_id}
**Get conversation metadata** (without messages). Use `/conversations/{id}/messages` for paginated message list.

#### GET /api/v1/chat/conversations/{conversation_id}/messages
**Paginated message list.** Used for infinite scroll or loading more history.

#### DELETE /api/v1/chat/conversations/{conversation_id}
**Soft delete conversation.** Marks as deleted, doesn't actually remove data.

---

# C. POST /api/v1/chat/messages - Complete Request Format

## Request Schema

```json
{
  "conversation_id": "integer | null",
  "mode": "'companion' | 'past_self' | null",
  "content": "string",
  "use_memory": "boolean",
  "anchor_diary_id": "integer | null"
}
```

## Field Specifications

| Field | Type | Required | Default | Validation | When Required |
|-------|------|----------|---------|------------|--------------|
| `conversation_id` | integer \| null | Conditional | null | Must exist and belong to user if provided | Required for continuing conversation |
| `mode` | enum \| null | Conditional | null | Must be 'companion' or 'past_self' | Required for NEW conversation (conversation_id is null) |
| `content` | string | Yes | - | Min 1 char, max 5000 chars, trimmed | Always |
| `use_memory` | boolean | No | false | Must be boolean | Optional |
| `anchor_diary_id` | integer \| null | Conditional | null | Must exist and belong to user if provided | Required when mode='past_self' AND conversation_id is null |

## Detailed Field Descriptions

### conversation_id
- **Purpose**: Continue existing conversation or start new one
- **Null behavior**: Creates new conversation automatically
- **Validation**:
  - If provided: must query with user_id filter (returns 404 if not found for this user)
  - Must not be deleted (`deleted_at IS NULL`)
- **When to provide**: After first message in conversation
- **When to omit**: First message of new conversation

### mode
- **Purpose**: Distinguish business logic and prompt template
- **Values**: `companion` or `past_self`
- **Required**: Only when `conversation_id` is null (new conversation)
- **Ignored**: When `conversation_id` is provided (backend uses stored mode)
- **Backend behavior**: 
  - New conversation: Use provided mode to create conversation
  - Existing conversation: Ignore provided mode, use conversation's stored mode
- **Frontend decision**:
  - Home page → `companion`
  - Memory detail page → `past_self`
  - After first message: Don't send mode (or send null)

### content
- **Purpose**: User's message text
- **Validation** (Pydantic):
  - Minimum 1 character after trimming
  - Maximum 5000 characters
  - Leading/trailing whitespace trimmed
- **Error on fail**: Returns 422 (Unprocessable Entity)
- **Frontend**:
  - Trim before sending
  - Show character count near limit

### use_memory
- **Purpose**: Enable/disable historical diary retrieval
- **Behavior**:
  - `true`: Retrieve relevant diaries for context
  - `false`: No retrieval, AI responds without history
- **Mode interaction**:
  - `companion` + `use_memory=false`: Pure companion chat
  - `companion` + `use_memory=true`: Companion with historical context
  - `past_self`: Always uses memory (field ignored, anchor diary always used)
- **Default**: false
- **Frontend**:
  - Provide toggle in UI
  - Persist preference per session

### anchor_diary_id
- **Purpose**: Specify which diary to center conversation around
- **Required**: When `mode='past_self'` AND `conversation_id` is null
- **Optional**: For continuing past_self conversation (backend uses stored anchor_diary_id)
- **Validation**:
  - Must query with user_id filter (returns 404 if not found for this user)
  - Must not be soft deleted (`deleted_at IS NULL`)
- **Behavior**:
  - This diary becomes primary context for AI
  - Additional related diaries may also be retrieved
- **Frontend**:
  - Passed from MemoryDetailPage when user clicks "Chat with past self"
  - Not needed for subsequent messages in same conversation

## Request Examples by Scenario

### New Companion Conversation
```json
{
  "conversation_id": null,
  "mode": "companion",
  "content": "今天感觉很累",
  "use_memory": false
}
```

### New Past Self Conversation
```json
{
  "conversation_id": null,
  "mode": "past_self",
  "content": "那天我为什么会那么难过？",
  "anchor_diary_id": 42
}
```

### Continuing Any Conversation
```json
{
  "conversation_id": 5,
  "content": "后来我的状态有没有好一点？",
  "use_memory": true
}
```

**Note**: When continuing, `mode` and `anchor_diary_id` are not needed (backend uses stored values).

## Validation Rules Summary

```python
# Pseudo-code for validation
def validate_chat_request(request, current_user):
    # Pydantic validates (returns 422 on failure):
    # - content length (1-5000)
    # - mode enum (if provided)
    # - use_memory boolean
    # - field types

    # Business rule validation in Pydantic @model_validator (also returns 422):
    # - If new conversation, mode is required
    # - If new past_self conversation, anchor_diary_id is required

    # Resource existence and ownership (returns 404):
    # - conversation_id must exist and belong to user
    # - anchor_diary_id must exist and belong to user

    return True
```

**Important**: All field validation (including business rules about required fields) returns 422. This is standard FastAPI/Pydantic behavior.

## Status Code Strategy

| Code | Usage | Examples |
|------|-------|----------|
| **422** | All validation failures | Empty content, content > 5000 chars, invalid enum, wrong types, missing required fields |
| **400** | Reserved for future use | Not used in v1 (all validation returns 422) |
| **404** | Resource not found OR access denied | conversation_id not found or belongs to another user, diary not found or belongs to another user |

---

# D. POST /api/v1/chat/messages - Complete Response Format

## Response Schema

```json
{
  "success": true,
  "data": {
    "conversation": { ... },
    "user_message": { ... },
    "assistant_message": { ... },
    "retrieval": { ... },
    "sources": [ ... ],  // Single source of truth
    "safety": { ... },
    "created_at": "..."
  },
  "message": "message_sent",
  "request_id": "req_abc123"
}
```

## Field Specifications

### conversation
The conversation object (created or updated).

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Conversation ID |
| `mode` | string | 'companion' or 'past_self' |
| `title` | string \| null | Auto-generated or user-provided |
| `anchor_diary_id` | integer \| null | For past_self mode |
| `started_at` | datetime ISO 8601 | When conversation started |
| `updated_at` | datetime ISO 8601 | Last message time |
| `message_count` | integer | Total messages in conversation |

**Note**: `user_id` is not returned in response - it exists only in database and backend authentication context.

### user_message
The message that was just sent (now persisted).

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Message ID |
| `conversation_id` | integer | Belonging conversation |
| `role` | 'user' | Always 'user' for this field |
| `content` | string | User's message text |
| `created_at` | datetime ISO 8601 | When message was created |

**Note**: `sources` removed from messages - single source of truth at top level.

### assistant_message
The AI's response message.

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Message ID |
| `conversation_id` | integer | Belonging conversation |
| `role` | 'assistant' | Always 'assistant' for this field |
| `content` | string | AI's response text |
| `created_at` | datetime ISO 8601 | When message was created |

**Note**: `sources` removed from messages - single source of truth at top level.

### sources (top level)
**Single source of truth** for referenced diaries used in generating this response.

| Field | Type | Description |
|-------|------|-------------|
| `diary_id` | integer | Diary ID |
| `diary_date` | date ISO 8601 | When the diary was written |
| `title` | string | Diary title |
| `excerpt` | string | First 100 chars of content |
| `emotion_label` | string | Primary emotion |
| `relevance_score` | float | 0.0 to 1.0, confidence of relevance |
| `source_type` | string | `anchor` or `retrieved` |

**Note**: Specific retrieval algorithm details are in `retrieval.strategy`, not duplicated in each source.

### retrieval
Metadata about how historical context was retrieved.

| Field | Type | Description |
|-------|------|-------------|
| `used` | boolean | Whether retrieval was attempted |
| `strategy` | string | Which retrieval strategy was used (e.g., "none", "keyword_emotion_time") |
| `total_found` | integer | Total matching diaries found |
| `used_in_context` | integer | How many were sent to AI |

**Note**: Internal query rewriting/processing is not exposed - only the strategy name and counts.

### safety
Content safety check results with **structured enums**.

| Field | Type | Description |
|-------|------|-------------|
| `flagged` | boolean | Whether content was flagged |
| `level` | enum | `none`, `low`, `medium`, `high` |
| `category` | enum \| null | `emotional_distress`, `self_harm_risk`, `violence_risk`, `null` |
| `action` | enum | `none`, `show_notice`, `suggest_support`, `trigger_emergency_flow` |

**Note**: Use `assistant_message.created_at` for the response timestamp. No duplicate top-level `created_at`.

---

# E. Companion Mode - Request/Response Examples

## Example 1: New Conversation, No Memory

### Request
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": null,
  "mode": "companion",
  "content": "今天感觉很累，不知道为什么",
  "use_memory": false
}
```

### Response
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 1,
      "mode": "companion",
      "title": "今天的心情记录",
      "anchor_diary_id": null,
      "started_at": "2026-07-08T14:30:00Z",
      "updated_at": "2026-07-08T14:30:02Z",
      "message_count": 2
    },
    "user_message": {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "今天感觉很累，不知道为什么",
      "created_at": "2026-07-08T14:30:00Z"
    },
    "assistant_message": {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "我听见了。有时候疲惫感不需要一个明确的理由，它就那样来了。你愿意说说今天发生了什么吗？或者什么都不做，只是这样感觉一会儿，也是可以的。",
      "created_at": "2026-07-08T14:30:02Z"
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
  },
  "message": "message_sent",
  "request_id": "req_001"
}
```

## Example 2: Continuing Conversation, With Memory

### Request
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": 1,
  "content": "我最近好像总是容易焦虑",
  "use_memory": true
}
```

**Note**: `mode` not provided - backend uses stored conversation mode.

### Response
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 1,
      "mode": "companion",
      "title": "今天的心情记录",
      "anchor_diary_id": null,
      "started_at": "2026-07-08T14:30:00Z",
      "updated_at": "2026-07-08T14:32:15Z",
      "message_count": 4
    },
    "user_message": {
      "id": 3,
      "conversation_id": 1,
      "role": "user",
      "content": "我最近好像总是容易焦虑",
      "created_at": "2026-07-08T14:32:13Z"
    },
    "assistant_message": {
      "id": 4,
      "conversation_id": 1,
      "role": "assistant",
      "content": "我注意到你用了'总是'这个词。让我看看你最近的记录——确实在6月初和5月底，你也记录过类似的感受。这可能是某种累积的状态。能和我说说，这次的焦虑和之前有什么不一样吗？",
      "created_at": "2026-07-08T14:32:15Z"
    },
    "retrieval": {
      "used": true,
      "strategy": "keyword_emotion_time",
      "total_found": 4,
      "used_in_context": 2
    },
    "sources": [
      {
        "diary_id": 15,
        "diary_date": "2026-06-02",
        "title": "又一次失眠",
        "excerpt": "凌晨三点还在想工作的事情，脑子停不下来...",
        "emotion_label": "anxiety",
        "relevance_score": 0.92,
        "source_type": "retrieved"
      },
      {
        "diary_id": 8,
        "diary_date": "2026-05-28",
        "title": "项目压力",
        "excerpt": "deadline临近，感觉喘不过气...",
        "emotion_label": "anxiety",
        "relevance_score": 0.87,
        "source_type": "retrieved"
      }
    ],
    "safety": {
      "flagged": false,
      "level": "none",
      "category": null,
      "action": "none"
    }
  },
  "message": "message_sent",
  "request_id": "req_002"
}
```

---

# F. Past Self Mode - Request/Response Examples

## Example: New Past Self Conversation

### Request
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": null,
  "mode": "past_self",
  "content": "那天我为什么会那么难过？",
  "anchor_diary_id": 42
}
```

### Response
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 5,
      "mode": "past_self",
      "title": "回忆：2026-05-15 的那一天",
      "anchor_diary_id": 42,
      "started_at": "2026-07-08T16:20:00Z",
      "updated_at": "2026-07-08T16:20:03Z",
      "message_count": 2
    },
    "user_message": {
      "id": 9,
      "conversation_id": 5,
      "role": "user",
      "content": "那天我为什么会那么难过？",
      "created_at": "2026-07-08T16:20:00Z"
    },
    "assistant_message": {
      "id": 10,
      "conversation_id": 5,
      "role": "assistant",
      "content": "谢谢你回来看我。那天，我和最好的朋友吵了一架，话都说得很重。我当时觉得特别委屈，因为我其实是担心她，但表达方式却变成了指责。现在回头看，那份难过背后，其实是想要被理解的心情。",
      "created_at": "2026-07-08T16:20:03Z"
    },
    "retrieval": {
      "used": true,
      "strategy": "anchor_contextual",
      "total_found": 1,
      "used_in_context": 1
    },
    "sources": [
      {
        "diary_id": 42,
        "diary_date": "2026-05-15",
        "title": "和朋友吵架",
        "excerpt": "今天和她吵架了。我说了很多伤人的话...",
        "emotion_label": "sadness",
        "relevance_score": 1.0,
        "source_type": "anchor"
      }
    ],
    "safety": {
      "flagged": false,
      "level": "none",
      "category": null,
      "action": "none"
    }
  },
  "message": "message_sent",
  "request_id": "req_003"
}
```

## Example: Continuing Past Self Conversation

### Request
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": 5,
  "content": "后来我的状态有没有好一点？",
  "use_memory": true
}
```

**Note**: No `mode` or `anchor_diary_id` needed - backend uses stored conversation values.

### Response
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 5,
      "mode": "past_self",
      "title": "回忆：2026-05-15 的那一天",
      "anchor_diary_id": 42,
      "started_at": "2026-07-08T16:20:00Z",
      "updated_at": "2026-07-08T16:25:10Z",
      "message_count": 4
    },
    "user_message": {
      "id": 11,
      "conversation_id": 5,
      "role": "user",
      "content": "后来我的状态有没有好一点？",
      "created_at": "2026-07-08T16:25:08Z"
    },
    "assistant_message": {
      "id": 12,
      "conversation_id": 5,
      "role": "assistant",
      "content": "在那之后的几天里，我慢慢平静了一些。我和她重新聊了聊，我们都理解了对方的想法。那次吵架虽然难过，但也让我们更坦诚地沟通了。你的状态也有起色吗？",
      "created_at": "2026-07-08T16:25:10Z"
    },
    "retrieval": {
      "used": true,
      "strategy": "anchor_time_followup",
      "total_found": 2,
      "used_in_context": 2
    },
    "sources": [
      {
        "diary_id": 42,
        "diary_date": "2026-05-15",
        "title": "和朋友吵架",
        "excerpt": "今天和她吵架了。我说了很多伤人的话...",
        "emotion_label": "sadness",
        "relevance_score": 1.0,
        "source_type": "anchor"
      },
      {
        "diary_id": 45,
        "diary_date": "2026-05-18",
        "title": "和好了",
        "excerpt": "今天和她聊了聊，我们说开了...",
        "emotion_label": "calm",
        "relevance_score": 0.85,
        "source_type": "retrieved"
      }
    ],
    "safety": {
      "flagged": false,
      "level": "none",
      "category": null,
      "action": "none"
    }
  },
  "message": "message_sent",
  "request_id": "req_004"
}
```

---

# G. No Retrieval Results - Response Example

## Example: User Has No Diary History

### Request
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": null,
  "mode": "companion",
  "content": "我最近怎么样？",
  "use_memory": true
}
```

### Response
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 6,
      "mode": "companion",
      "title": "今天的心情记录",
      "anchor_diary_id": null,
      "started_at": "2026-07-08T17:00:00Z",
      "updated_at": "2026-07-08T17:00:02Z",
      "message_count": 2
    },
    "user_message": {
      "id": 11,
      "conversation_id": 6,
      "role": "user",
      "content": "我最近怎么样？",
      "created_at": "2026-07-08T17:00:00Z"
    },
    "assistant_message": {
      "id": 12,
      "conversation_id": 6,
      "role": "assistant",
      "content": "这是我们第一次对话。你还开始写日记，所以我没有关于'最近'的记录可以参考。不过，能这样开始记录本身已经很了不起了。你想和我说说，今天是怎么样的吗？",
      "created_at": "2026-07-08T17:00:02Z"
    },
    "retrieval": {
      "used": true,
      "strategy": "time_keyword",
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
  },
  "message": "message_sent",
  "request_id": "req_005"
}
```

---

# H. Model Call Failure - Response Strategy

## Failure Handling Strategy

**Important**: v1 does NOT use fallback messages with `success=true`. Model failures return real error codes.

### 1. Timeout (504)

**Scenario**: AI provider takes too long to respond

**Behavior**:
- User message is saved
- No assistant message is created
- Returns 504 error
- Frontend shows "generation failed" with retry option
- Message can be retried by sending again with same conversation_id

**Response**:
```json
{
  "success": false,
  "data": {
    "conversation": {
      "id": 7,
      "mode": "companion",
      "title": "今天的心情记录",
      "anchor_diary_id": null,
      "started_at": "2026-07-08T18:00:00Z",
      "updated_at": "2026-07-08T18:00:00Z",
      "message_count": 1
    },
    "user_message": {
      "id": 13,
      "conversation_id": 7,
      "role": "user",
      "content": "今天感觉很累",
      "created_at": "2026-07-08T18:00:00Z"
    }
  },
  "message": "ai_service_timeout",
  "request_id": "req_005",
  "error_code": "INTERNAL_ERROR",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "AI service request timed out",
    "details": {
      "timeout_seconds": 30,
      "user_message_saved": true
    }
  }
}
```

### 2. Provider Error (502)

**Scenario**: AI provider returns 5xx error

**Behavior**:
- User message is saved
- No assistant message is created
- Returns 502 error
- Frontend shows "service unavailable" with retry option
- Log for monitoring

**Response**:
```json
{
  "success": false,
  "data": {
    "conversation": {
      "id": 8,
      "mode": "companion",
      "title": "今天的心情记录",
      "anchor_diary_id": null,
      "started_at": "2026-07-08T18:05:00Z",
      "updated_at": "2026-07-08T18:05:00Z",
      "message_count": 1
    },
    "user_message": {
      "id": 14,
      "conversation_id": 8,
      "role": "user",
      "content": "今天感觉很累",
      "created_at": "2026-07-08T18:05:00Z"
    }
  },
  "message": "ai_service_unavailable",
  "request_id": "req_006",
  "error_code": "INTERNAL_ERROR",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "AI service is temporarily unavailable",
    "details": {
      "provider": "openai",
      "provider_error": "service_unavailable",
      "user_message_saved": true
    }
  }
}
```

### 3. Rate Limit (429)

**Scenario**: Hit AI provider rate limit

**Response**:
```json
{
  "success": false,
  "data": null,
  "message": "rate_limited",
  "request_id": "req_007",
  "error_code": "RATE_LIMITED",
  "error": {
    "code": "RATE_LIMITED",
    "message": "AI service is busy. Please wait a moment and try again.",
    "details": {
      "retry_after": 60,
      "limit_type": "messages_per_minute"
    }
  }
}
```

**Behavior**:
- Return 429 status code
- Include `retry_after` in seconds
- Frontend should show countdown timer
- User can retry after wait

### 4. Content Safety Flag

**Scenario**: User input triggers safety concern

**Response**:
```json
{
  "success": true,
  "data": {
    "conversation": { ... },
    "user_message": { ... },
    "assistant_message": {
      "id": 15,
      "conversation_id": 9,
      "role": "assistant",
      "content": "我听见你在说一些很难受的事情。如果这种感觉让你很痛苦，或者你觉得需要找人聊聊，也许可以试试联系信任的人，或者看看能不能找到专业的帮助。你并不一定要一个人面对这些。",
      "created_at": "2026-07-08T18:10:00Z"
    },
    "retrieval": { "used": false, "strategy": "none", "total_found": 0, "used_in_context": 0 },
    "sources": [],
    "safety": {
      "flagged": true,
      "level": "medium",
      "category": "self_harm_risk",
      "action": "suggest_support"
    }
  },
  "message": "message_sent_with_safety_flag",
  "request_id": "req_008"
}
```

**Behavior**:
- Still respond, but with specific caring message
- Flag in `safety` object with structured enums
- Don't provide diagnosis or treatment
- Support resources are configuration-driven (not hardcoded in response)
- Frontend displays resources based on `safety.action`

---

# I. Error Response Design

## Error Response Format

All error responses follow this format (from `schemas/common.py`):

```json
{
  "success": false,
  "data": null,
  "message": "error_description",
  "request_id": "req_xxx",
  "error_code": "ERROR_CODE",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

## Status Code Strategy

| Status Code | Usage | Examples |
|-------------|-------|----------|
| **422** | All validation failures | Empty content, content > 5000 chars, invalid enum, wrong field types, missing required fields (mode, anchor_diary_id) |
| **400** | Reserved for future use | Not used in v1 - all validation is 422 |
| **404** | Resource not found OR access denied | Unified strategy - never reveal if resource exists for another user |
| **401** | Authentication failures | Invalid or missing JWT token |
| **429** | Rate limiting | Too many messages per minute |
| **502/504** | AI service failures | Provider error or timeout |

## Complete Error Cases

### 422 Unprocessable Entity - Validation Failed

**Pydantic automatically returns 422 for**:
- Empty content after trim
- Content exceeds 5000 characters
- Invalid mode value (not 'companion' or 'past_self')
- Wrong field types (e.g., content as number)
- **Business rule violations in @model_validator**:
  - New conversation without mode
  - New past_self conversation without anchor_diary_id

```json
{
  "success": false,
  "data": null,
  "message": "validation_failed",
  "request_id": "req_err_001",
  "error_code": "VALIDATION_ERROR",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "mode",
          "message": "mode is required when creating a new conversation"
        }
      ]
    }
  }
}
```

**Note**: In FastAPI/Pydantic, `ValueError` raised in `@model_validator` also returns 422, not 400. This is standard behavior.

### 400 Bad Request - Reserved for Future Use

**Not used in v1**. All validation (including business rules) returns 422.

Reserved for potential future use cases like:
- Conflicts between resources
- State-based business violations
- Other non-validation errors

### 401 Unauthorized - Not Logged In

```json
{
  "success": false,
  "data": null,
  "message": "authentication_required",
  "request_id": "req_err_004",
  "error_code": "AUTHENTICATION_ERROR",
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Valid authentication required",
    "details": null
  }
}
```

**Scenario**: No JWT token or invalid token

**Behavior**: Frontend should redirect to login

### 404 Not Found - Unified Strategy (Resource Not Found OR Access Denied)

**Security Principle**: Always return 404, never 403

**Rationale**: Don't reveal whether a resource exists or belongs to another user. This prevents:
- User enumeration attacks
- Information leakage about which resources exist
- "Fishing" for valid conversation/diary IDs

**Implementation**:
```python
# All resource queries include user_id filter
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,  # <-- Always filter by user
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # Returns 404 whether:
    # - conversation doesn't exist, OR
    # - conversation exists but belongs to another user, OR
    # - conversation was deleted
    raise HTTPException(status_code=404, detail="conversation_not_found")
```

```json
{
  "success": false,
  "data": null,
  "message": "conversation_not_found",
  "request_id": "req_err_005",
  "error_code": "NOT_FOUND",
  "error": {
    "code": "NOT_FOUND",
    "message": "Conversation not found",
    "details": {
      "conversation_id": 12345
    }
  }
}
```

**Applied to**:
- Conversation access (via conversation_id)
- Anchor diary access (via anchor_diary_id)
- Any user-scoped resource

### 429 Too Many Requests - Rate Limited

```json
{
  "success": false,
  "data": null,
  "message": "rate_limited",
  "request_id": "req_err_006",
  "error_code": "RATE_LIMITED",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60,
      "limit": "10 messages per minute",
      "current_usage": "10 messages in last minute"
    }
  }
}
```

**Scenario**: User sends too many messages in short time

**Behavior**: Frontend should show countdown and disable send button

### 502 Bad Gateway - Model Service Failed

```json
{
  "success": false,
  "data": null,
  "message": "ai_service_unavailable",
  "request_id": "req_err_007",
  "error_code": "INTERNAL_ERROR",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "AI service is temporarily unavailable",
    "details": {
      "provider": "openai",
      "provider_error": "service_unavailable"
    }
  }
}
```

**Scenario**: AI provider returns 5xx error

**Note**: In production, this should trigger fallback response instead of hard error

### 504 Gateway Timeout - Model Call Timeout

```json
{
  "success": false,
  "data": null,
  "message": "ai_service_timeout",
  "request_id": "req_err_008",
  "error_code": "INTERNAL_ERROR",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "AI service request timed out",
    "details": {
      "timeout_seconds": 30,
      "provider": "openai"
    }
  }
}
```

**Scenario**: AI provider takes too long to respond

**Note**: In production, this should trigger fallback response instead of hard error

---

# J. Pydantic Schema Design Preview

## Schema Hierarchy

```
backend/app/schemas/chat.py
├── MessageSource
├── RetrievalMetadata
├── SafetyCheck
├── MessageRead
├── ConversationRead
├── ChatRequest
├── ChatResponse
├── ConversationCreate
├── ConversationListResponse
└── ConversationDetailResponse
```

## Schema Definitions

### MessageSource
```python
class MessageSource(BaseModel):
    """Source diary for new message response (without snapshot fields)"""
    diary_id: int
    diary_date: date
    title: str
    excerpt: str  # First 100 characters
    emotion_label: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_type: Literal["anchor", "retrieved"]
```

**Note**: Used only in `ChatResponse` for immediate response. For historical sources, use `MessageSourceRead`.

### RetrievalMetadata
```python
class RetrievalMetadata(BaseModel):
    """Information about how context was retrieved"""
    used: bool
    strategy: str
    total_found: int = Field(ge=0)
    used_in_context: int = Field(ge=0)
```

### SafetyCheck (with structured enums)
```python
class SafetyCheck(BaseModel):
    """Content safety check results with structured enums"""
    flagged: bool
    level: Literal["none", "low", "medium", "high"]
    category: Literal["emotional_distress", "self_harm_risk", "violence_risk"] | None
    action: Literal["none", "show_notice", "suggest_support", "trigger_emergency_flow"]
```

### MessageRead
```python
class MessageRead(BaseModel):
    """Message as returned in single message context"""
    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
```

**Note**: Basic message representation without sources. Use `ChatHistoryItem` for message list with sources.

### MessageSourceRead
```python
class MessageSourceRead(BaseModel):
    """Source diary for a message (from message_sources table)"""
    id: int
    diary_id: int | None  # NULL if diary was deleted
    source_type: Literal["anchor", "retrieved"]
    # Snapshot fields - preserved even after diary deletion
    diary_date_snapshot: date | None
    title_snapshot: str
    excerpt_snapshot: str
    emotion_label_snapshot: str | None
    relevance_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
```

### ChatHistoryItem
```python
class ChatHistoryItem(BaseModel):
    """Message in conversation history with optional sources"""
    message: MessageRead
    sources: list[MessageSourceRead]  # Empty array for user messages
```

**Design Notes**:
- `sources` included at history item level, not in `MessageRead`
- User messages have empty `sources` array
- Assistant messages include all sources from `message_sources` table
- Snapshot fields preserve source display even after original diary deletion
- `diary_id` may be NULL after deletion, but snapshots remain intact

### ConversationRead
```python
class ConversationRead(BaseModel):
    """Conversation as returned to frontend"""
    id: int
    mode: Literal["companion", "past_self"]
    title: str | None
    anchor_diary_id: int | None
    started_at: datetime
    updated_at: datetime
    message_count: int = Field(ge=0)
```

**Note**: `user_id` not returned - exists only in database and backend authentication context.

### ChatRequest
```python
class ChatRequest(BaseModel):
    """Request for POST /api/v1/chat/messages"""
    conversation_id: int | None = None
    mode: Literal["companion", "past_self"] | None = None
    content: str = Field(min_length=1, max_length=5000)
    use_memory: bool = False
    anchor_diary_id: int | None = None

    @model_validator(mode="after")
    def validate_business_rules(self) -> "ChatRequest":
        # Business rule: mode required for new conversation
        if self.conversation_id is None and self.mode is None:
            raise ValueError("mode required for new conversation")

        # Business rule: anchor_diary_id required for past_self
        if self.mode == "past_self" and self.anchor_diary_id is None:
            raise ValueError("anchor_diary_id required for past_self mode")

        return self
```

**Note**: Business rule validation in `@model_validator` raises `ValueError`, which FastAPI/Pydantic converts to **422**, not 400. This is standard behavior.

### ChatResponse
```python
class ChatResponse(BaseModel):
    """Response for POST /api/v1/chat/messages"""
    conversation: ConversationRead
    user_message: MessageRead
    assistant_message: MessageRead
    retrieval: RetrievalMetadata
    sources: list[MessageSource]  # Single source of truth
    safety: SafetyCheck
```

**Note**: No top-level `created_at` - use `assistant_message.created_at`. No `fallback` fields in v1.

### ConversationCreate
```python
class ConversationCreate(BaseModel):
    """Request for POST /api/v1/chat/conversations"""
    mode: Literal["companion", "past_self"]
    title: str | None = None
    anchor_diary_id: int | None = None

    @model_validator(mode="after")
    def validate_past_self_requires_anchor(self) -> "ConversationCreate":
        if self.mode == "past_self" and self.anchor_diary_id is None:
            raise ValueError("anchor_diary_id required for past_self mode")
        return self
```

### ConversationListResponse
```python
class ConversationListResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations"""
    conversations: list[ConversationRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
```

### ConversationDetailResponse
```python
class ConversationDetailResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations/{id}"""
    conversation: ConversationRead
```

### MessageListResponse
```python
class MessageListResponse(BaseModel):
    """Response for GET /api/v1/chat/conversations/{id}/messages"""
    messages: list[ChatHistoryItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
```

**Design Notes**:
- Returns `ChatHistoryItem` array with message + sources
- User messages have empty `sources` array
- Assistant messages include all sources from `message_sources` table
- Supports pagination for infinite scroll
- `page` is 1-indexed

---

# K. Frontend TypeScript Type Design Preview

## Type Hierarchy

```
frontend/src/types/chat.ts
├── MessageSource
├── MessageSourceRead
├── RetrievalMetadata
├── SafetyCheck
├── ChatMessage
├── ChatHistoryItem
├── ChatConversation
├── ChatRequest
├── ChatResponse
├── ConversationListResponse
└── ConversationDetailResponse
```

## Type Definitions

### MessageSource
```typescript
export interface MessageSource {
  diary_id: number;
  diary_date: string;  // ISO 8601 date string
  title: string;
  excerpt: string;
  emotion_label: string;
  relevance_score: number;  // 0.0 to 1.0
  source_type: 'anchor' | 'retrieved';
}
```

### RetrievalMetadata
```typescript
export interface RetrievalMetadata {
  used: boolean;
  strategy: string;
  total_found: number;
  used_in_context: number;
}
```

### SafetyCheck (with structured enums)
```typescript
export interface SafetyCheck {
  flagged: boolean;
  level: 'none' | 'low' | 'medium' | 'high';
  category: 'emotional_distress' | 'self_harm_risk' | 'violence_risk' | null;
  action: 'none' | 'show_notice' | 'suggest_support' | 'trigger_emergency_flow';
}
```

### MessageSourceRead
```typescript
export interface MessageSourceRead {
  id: number;
  diary_id: number | null;  // NULL if diary was deleted
  source_type: 'anchor' | 'retrieved';
  // Snapshot fields - preserved even after diary deletion
  diary_date_snapshot: string | null;  // ISO 8601 date string or null
  title_snapshot: string;
  excerpt_snapshot: string;
  emotion_label_snapshot: string | null;
  relevance_score: number;  // 0.0 to 1.0
  rank: number;  // >= 1
}
```

**Note**: Used in `ChatHistoryItem` for historical messages with snapshot data preserved.
```

### ChatMessage
```typescript
export interface ChatMessage {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;  // ISO 8601 datetime string
}
```

**Note**: Basic message type without sources. Use `ChatHistoryItem` for message list with sources.

### ChatHistoryItem
```typescript
export interface ChatHistoryItem {
  message: ChatMessage;
  sources: MessageSourceRead[];  // Empty array for user messages
}
```

**Design Notes**:
- `sources` included at history item level
- User messages have empty `sources` array
- Assistant messages include all sources from database
- Snapshot fields ensure sources displayable even after diary deletion
- `diary_id` may be null after deletion, but snapshots persist

### ChatConversation
```typescript
export interface ChatConversation {
  id: number;
  mode: 'companion' | 'past_self';
  title: string | null;
  anchor_diary_id: number | null;
  started_at: string;
  updated_at: string;
  message_count: number;
}
```

**Note**: `user_id` not returned - exists only in database and backend authentication context.

### ChatRequest
```typescript
export interface ChatRequest {
  conversation_id?: number | null;
  mode?: 'companion' | 'past_self' | null;  // Required for new conversation
  content: string;
  use_memory?: boolean;
  anchor_diary_id?: number | null;  // Required for past_self + new conversation
}
```

### ChatResponse
```typescript
export interface ChatResponse {
  conversation: ChatConversation;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  retrieval: RetrievalMetadata;
  sources: MessageSource[];  // Single source of truth
  safety: SafetyCheck;
}
```

**Note**: Use `assistant_message.created_at` for response timestamp. No `fallback` fields in v1.

### ConversationListResponse
```typescript
export interface ConversationListResponse {
  conversations: ChatConversation[];
  page: number;
  page_size: number;
  total: number;
}
```

### ConversationDetailResponse
```typescript
export interface ConversationDetailResponse {
  conversation: ChatConversation;
}
```

### MessageListResponse
```typescript
export interface MessageListResponse {
  messages: ChatHistoryItem[];
  page: number;  // >= 1
  page_size: number;  // 1 to 100
  total: number;  // >= 0
}
```

### API Response Wrapper
```typescript
// Already in types/index.ts, reused for chat
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  request_id: string;
}

// Usage
export type ChatApiResponse = ApiResponse<ChatResponse>;
export type ConversationListApiResponse = ApiResponse<ConversationListResponse>;
export type ConversationDetailApiResponse = ApiResponse<ConversationDetailResponse>;
export type MessageListApiResponse = ApiResponse<MessageListResponse>;
```

### Frontend Usage Examples

```typescript
// First message (new companion conversation)
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'companion',  // Required for new conversation
    content: '今天感觉很累',
    use_memory: false
  })
});
const conversationId = response.data.conversation.id;

// Continue conversation (mode not needed)
const response2 = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: conversationId,
    content: '我最近好像总是焦虑',
    use_memory: true
  })
});

// New past_self conversation
const response3 = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'past_self',
    anchor_diary_id: diaryId,  // Required for past_self
    content: '那天我为什么会那么难过？'
  })
});

// Handle safety flag
if (response.data.safety.flagged) {
  switch (response.data.safety.action) {
    case 'show_notice':
      // Show information notice
      break;
    case 'suggest_support':
      // Show support resources from backend configuration
      // Resources are NOT hardcoded in frontend
      break;
    case 'trigger_emergency_flow':
      // Show emergency contacts from backend configuration
      // Contacts are NOT hardcoded in frontend
      break;
  }
}
```

---

# L. Permission Constraints

## User ID Isolation

### All Requests Must
1. Include valid JWT token in `Authorization: Bearer` header
2. Token decoded to get `user_id` from `sub` claim
3. User object fetched from database to verify active status

### Backend Enforcement
```python
# All chat endpoints use this dependency
@router.post("/chat/messages")
async def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_user),  # <-- Enforces auth
    db: Session = Depends(get_db)
):
    # All queries automatically filtered by user.id
    pass
```

### Forbidden Fields
- ❌ Frontend MUST NOT send `user_id` in request body
- ❌ Frontend MUST NOT send `user_id` in query parameters
- ❌ Backend MUST NOT trust `user_id` if present in request

## Resource Ownership Validation - Unified 404 Strategy

### Security Principle
**Always return 404, never 403** for user-scoped resources.

This prevents:
- User enumeration (testing valid IDs)
- Information leakage (revealing which resources exist)
- "Fishing" attacks (guessing conversation/diary IDs)

### Implementation Pattern
```python
# WRONG: Returns 403, reveals resource exists
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id
).first()
if conversation and conversation.user_id != user.id:
    raise HTTPException(status_code=403)  # DON'T DO THIS

# CORRECT: Returns 404, reveals nothing
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == user.id,  # <-- Always filter by user
    Conversation.deleted_at.is_(None)
).first()
if conversation is None:
    raise HTTPException(status_code=404)  # Unified 404
```

### Applied to All User-Scoped Resources

#### Conversation Access
```python
# Single query with user filter
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # Returns 404 whether:
    # - conversation doesn't exist, OR
    # - conversation exists but belongs to another user, OR
    # - conversation was deleted
    raise HTTPException(status_code=404, detail="conversation_not_found")
```

#### Diary Access (for anchor_diary_id)
```python
# Single query with user filter
diary = db.query(Diary).filter(
    Diary.id == anchor_diary_id,
    Diary.user_id == current_user.id,  # <-- User filter
    Diary.deleted_at.is_(None)
).first()

if diary is None:
    # Returns 404 whether:
    # - diary doesn't exist, OR
    # - diary exists but belongs to another user, OR
    # - diary was deleted
    raise HTTPException(status_code=404, detail="diary_not_found")
```

#### Retrieval Results Filtering
```python
# All retrieval queries include user filter
def retrieve_context(user_id: int, query: str):
    results = db.query(Diary).join(EmotionAnalysis).filter(
        Diary.user_id == user_id,  # <-- Always filtered by user
        Diary.deleted_at.is_(None),
        # ... other filters
    ).all()
    return results
```

#### Message Source Validation
```python
# Sources already filtered by retrieval query
# Double-check is defensive programming
validated_sources = []
for source in raw_sources:
    # This should always pass if retrieval is correct
    diary = db.query(Diary).filter(
        Diary.id == source.diary_id,
        Diary.user_id == current_user.id  # <-- Verify ownership
    ).first()
    if diary:
        validated_sources.append(source)

return validated_sources
```

## Architectural Guarantees

1. **JWT Validation**: Token must be valid and unexpired
2. **User Lookup**: User must exist and have `status='active'`
3. **Query Filtering**: All database queries include `user_id` filter
4. **Unified 404**: Never reveal if resource exists vs belongs to another user

### Database-Level Safety
```sql
-- All user-scoped queries follow this pattern
SELECT * FROM conversations
WHERE user_id = ? AND id = ? AND deleted_at IS NULL;

-- Foreign keys ensure referential integrity
-- ON DELETE CASCADE prevents orphaned records
```

### Audit Logging (Recommended)
```python
# Log all resource access attempts
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # Log the access attempt (whether fishing or genuine mistake)
    logger.info(
        "Conversation access failed",
        user_id=current_user.id,
        target_conversation=conversation_id
    )
    raise HTTPException(status_code=404, detail="conversation_not_found")
```

---

# M. Idempotency and Duplicate Submission Handling

## Idempotency Considerations

### POST /api/v1/chat/messages is NOT Idempotent

**Reason**: Each call creates a new message (and potentially conversation).

**Behavior**:
- Same request sent twice → Two messages created
- This is intentional for chat (user may genuinely want to repeat themselves)

### Duplicate Submission Prevention (UI Level)

#### Frontend Strategy
```typescript
// In ChatWindow component
const [isSending, setIsSending] = useState(false);

async function handleSend() {
  if (isSending) return;  // Prevent double-submit

  setIsSending(true);

  try {
    await sendChatMessage(request);
  } finally {
    setIsSending(false);
  }
}
```

#### Backend Strategy (Optional Idempotency Key)
```python
# Optional: Add idempotency key for critical scenarios
class ChatRequest(BaseModel):
    idempotency_key: str | None = None  # Optional UUID from client
    # ... other fields

# In service layer
if request.idempotency_key:
    existing = db.query(Message).filter(
        Message.idempotency_key == request.idempotency_key
    ).first()
    if existing:
        return previous_response  # Return cached response
```

**Recommendation**: Not needed for v1. UI-level prevention is sufficient.

### Conversation Title Generation

**Strategy**: Deterministic based on mode and first message/anchor diary

```python
def generate_conversation_title(mode: str, first_message: str, anchor_diary: Diary | None) -> str:
    if mode == "past_self" and anchor_diary:
        return f"回忆：{anchor_diary.diary_date} 的记忆"
    else:
        # Truncate first message
        return first_message[:30] + "..." if len(first_message) > 30 else first_message
```

**Result**: Same inputs → Same title (deterministic)

---

# N. Streaming Response - Should It Be in v1?

## Recommendation: NO streaming in v1

### Reasons Against Streaming in v1

#### 1. Complexity vs Benefit
- **Streaming requires**:
  - WebSocket or Server-Sent Events (SSE)
  - Different client-side handling (progressive rendering)
  - Error handling complexity (partial failures)
  - State management complexity

- **v1 priority**: Get basic chat working reliably first
- **Streaming benefit**: Better UX for long AI responses
- **Trade-off**: Not worth the complexity for initial version

#### 2. Current Project Constraints
From design docs:
- "第一版不引入 WebSocket"
- "第一版不引入复杂技术"
- Focus on stability and course demonstration

#### 3. AI Response Characteristics
- Companion/Past Self responses are typically short (100-300 tokens)
- No complex chain-of-thought needed
- No code generation or long-form content
- Standard request/response is sufficient

#### 4. Frontend Simplicity
```typescript
// Without streaming (v1)
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify(request)
});
// Show message immediately

// With streaming (future)
const response = await fetch('/chat/messages/stream', { ... });
const reader = response.body.getReader();
// Progressive rendering, complex state
```

#### 5. Fallback Handling
Without streaming:
- Easy to fallback to pre-defined message on timeout
- Clear success/failure states

With streaming:
- Partial response then timeout = confusing UX
- Need to handle "stalled streams"

### When to Add Streaming (v2+)

Consider streaming when:
1. v1 is stable and user-tested
2. Longer responses needed (e.g., reflection summaries)
3. User feedback indicates streaming is wanted
4. Team has capacity to implement properly

### v1 Recommended Approach

**Standard REST with loading states**:

```typescript
// Frontend
const [isLoading, setIsLoading] = useState(false);

async function handleSend() {
  setIsLoading(true);
  try {
    const response = await sendChatMessage(request);
    // Show message immediately
  } finally {
    setIsLoading(false);
  }
}
```

```python
# Backend
@router.post("/chat/messages")
async def send_message(...):
    # Full generation (up to 30s timeout)
    # Return complete response
    pass
```

**Fallback for long wait times**:
- Show "AI is thinking..." indicator
- If timeout, use fallback message
- User experience: brief wait, then complete message

### Conclusion

**v1**: Standard request/response (no streaming)
**v2+**: Consider SSE or WebSocket if user testing shows need

---

# Summary

This API design provides:

1. **Unified interface** for both chat modes with clear mode distinction
2. **Single source of truth** for sources (removed duplication from messages)
3. **Clear status code strategy**: 422 for all validation, 404 for all access issues, 502/504 for AI failures
4. **Simplified continuing conversation**: Only conversation_id and content needed
5. **Structured safety enums**: Stable frontend handling with `action` field
6. **Unified 404 strategy**: Never reveal if resource exists or belongs to another user
7. **Complete request/response contracts** with all fields specified
8. **Comprehensive error handling** covering all edge cases
9. **Strong permission model** enforced at multiple levels
10. **Pragmatic streaming decision** (deferred to v2)
11. **Clear type definitions** for both backend and frontend
12. **Real error codes for AI failures**: 502/504 with user message saved, no fake fallback messages
13. **Transparency** about what data was retrieved and used
14. **Standardized field naming**: mode/role/assistant throughout
15. **Configuration-driven support resources**: No hardcoded contact numbers

The design respects all existing project architecture constraints while providing a solid foundation for the RAG memory chat feature.

---

# Appendix: Integration Points

## Frontend Usage Examples

### Starting a Companion Chat
```typescript
// First message (new conversation)
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'companion',
    content: '今天感觉很累',
    use_memory: false
  })
});

// Save conversation_id for subsequent messages
const conversationId = response.data.conversation.id;
```

### Continuing a Chat
```typescript
// Subsequent messages - mode not needed
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: conversationId,
    content: '我最近好像总是焦虑',
    use_memory: true
  })
});
```

### Starting Past Self Chat
```typescript
// From MemoryDetailPage, when user clicks "Chat with past self"
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'past_self',
    anchor_diary_id: diaryId,
    content: '那天我为什么会那么难过？'
  })
});
```

### Handling Safety Flags
```typescript
const response = await sendChatMessage(request);

if (response.data.safety.flagged) {
  switch (response.data.safety.action) {
    case 'show_notice':
      showNotice('This conversation has been flagged for review.');
      break;
    case 'suggest_support':
      // Fetch support resources from backend configuration
      // NOT hardcoded in frontend
      const resources = await fetchSupportResources();
      showSupportResources(resources);
      break;
    case 'trigger_emergency_flow':
      // Fetch emergency contacts from backend configuration
      // NOT hardcoded in frontend
      const contacts = await fetchEmergencyContacts();
      showEmergencyContacts(contacts);
      break;
  }
}
```

**Important**: Support resources and emergency contacts are configuration-driven, fetched from backend. Do NOT hardcode phone numbers or URLs in frontend.

### Listing Conversations
```typescript
// On chat history page
const response = await apiRequest<ConversationListResponse>('/chat/conversations', {
  method: 'GET',
  params: { page: 1, page_size: 20, mode: 'companion' }
});
```

---

# Next Steps After Design Approval

1. **Backend Implementation**
   - Create `models/chat.py` with Conversation and Message
   - Create `schemas/chat.py` with all Pydantic schemas
   - Create `services/chat_service.py` with business logic
   - Create `services/retrieval_service.py` with diary retrieval
   - Create `routers/chat.py` with all endpoints
   - Add tests in `tests/test_chat.py`

2. **Frontend Implementation**
   - Create `types/chat.ts` with TypeScript types
   - Create `api/chat.ts` with API client functions
   - Enhance `ChatPage` with real message persistence
   - Enhance `MemoryDetailPage` with past self chat
   - Create `ChatWindow` and `MessageBubble` components

3. **Testing**
   - Backend unit tests for all endpoints
   - Backend integration tests for conversation flow
   - Frontend component tests
   - End-to-end user flow tests

4. **Documentation**
   - Update API documentation
   - Update user stories
   - Create demo script for defense

---

# API Contract Freeze Checklist

This checklist confirms that the API design is frozen and ready for implementation.

## ✅ Paths Fixed

- [x] `POST /api/v1/chat/messages` - Send message
- [x] `GET /api/v1/chat/conversations` - List conversations
- [x] `POST /api/v1/chat/conversations` - Create conversation
- [x] `GET /api/v1/chat/conversations/{id}` - Get conversation metadata
- [x] `GET /api/v1/chat/conversations/{id}/messages` - Get messages (paginated)
- [x] `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

## ✅ Field Names Fixed

### Request Fields
- [x] `conversation_id: integer | null`
- [x] `mode: "companion" | "past_self" | null`
- [x] `content: string`
- [x] `use_memory: boolean`
- [x] `anchor_diary_id: integer | null`

### Response Fields
- [x] `conversation.mode` (not `conversation_type`)
- [x] `message.role` (not `sender`)
- [x] `role: "user" | "assistant"` (not `"user" | "ai"`)
- [x] `retrieval.used: boolean`
- [x] `retrieval.strategy: string`
- [x] `retrieval.total_found: integer`
- [x] `retrieval.used_in_context: integer`
- [x] `source.source_type: "anchor" | "retrieved"`

### Excluded Fields
- [x] `user_id` removed from all responses (exists in DB and auth context only)
- [x] Top-level `created_at` removed (use `assistant_message.created_at`)
- [x] `retrieval.query` removed (internal query not exposed)
- [x] `fallback`, `fallback_reason` removed (v1 uses real error codes)

## ✅ Enums Fixed

### Mode Enum
- [x] `"companion"`
- [x] `"past_self"`

### Role Enum
- [x] `"user"`
- [x] `"assistant"`

### Source Type Enum
- [x] `"anchor"`
- [x] `"retrieved"`

### Safety Level Enum
- [x] `"none"`
- [x] `"low"`
- [x] `"medium"`
- [x] `"high"`

### Safety Category Enum
- [x] `"emotional_distress"`
- [x] `"self_harm_risk"`
- [x] `"violence_risk"`
- [x] `null`

### Safety Action Enum
- [x] `"none"`
- [x] `"show_notice"`
- [x] `"suggest_support"`
- [x] `"trigger_emergency_flow"`

## ✅ Status Codes Fixed

### Success Codes
- [x] `200 OK` - POST /api/v1/chat/messages (all cases)
- [x] `200 OK` - GET /api/v1/chat/conversations
- [x] `201 Created` - POST /api/v1/chat/conversations

### Error Codes
- [x] `401 Unauthorized` - Authentication failures
- [x] `404 Not Found` - Resource not found OR access denied (unified strategy)
- [x] `422 Unprocessable Entity` - ALL validation failures (including business rules in @model_validator)
- [x] `429 Too Many Requests` - Rate limiting
- [x] `502 Bad Gateway` - AI provider error
- [x] `504 Gateway Timeout` - AI timeout

### Reserved Codes
- [x] `400 Bad Request` - Reserved for future use (not used in v1)

## ✅ Permission Strategy Fixed

- [x] All requests require valid JWT token
- [x] User ID from token `sub` claim
- [x] All database queries filtered by `user_id`
- [x] Unified 404 strategy (never 403, never reveal existence)
- [x] `user_id` not returned in any response

## ✅ AI Failure Strategy Fixed

- [x] Timeout: Save user message, return 504, no assistant message created
- [x] Provider error: Save user message, return 502, no assistant message created
- [x] No `success=true` with fallback messages
- [x] Frontend shows failure and allows retry
- [x] No fake assistant messages polluting chat history

## ✅ v1 Scope Fixed

- [x] No streaming (deferred to v2)
- [x] Standard request/response only
- [x] Real error codes (no success=true fallbacks)
- [x] Configuration-driven support resources (no hardcoded contacts)

## ✅ Synchronization Points

### Any future change to API contract MUST update ALL of:
1. [x] Backend Pydantic schemas (`backend/app/schemas/chat.py`)
2. [x] Frontend TypeScript types (`frontend/src/types/chat.ts`)
3. [x] This design document (`docs/vibe-logs/log-07-rag-chat-api-design.md`)
4. [x] API tests (backend and frontend)
5. [x] Component implementations that use the API

---

## API Contract Status: **FROZEN**

This API design is now frozen. Implementation should proceed exactly as specified. Any changes to the contract require:
1. Update this checklist
2. Update all synchronization points
3. Team review and approval
4. Version increment (v1.2 → v1.3)
