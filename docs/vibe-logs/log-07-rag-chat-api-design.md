# Inner Garden Chat API 设计文档

## 版本：1.2.1（历史来源支持）
## 日期：2026-07-08
## 状态：设计阶段 - 数据库模式已固定

## 更新日志
- v1.2.1：新增历史消息来源支持 - ChatHistoryItem 现在包含 assistant 消息的来源，与 MessageRead 分离以避免循环依赖
- v1.2：API 契约冻结 - 固定状态码策略（Pydantic 验证器返回 422），统一 AI 失败处理（返回 502/504 而非 success=true），标准化字段命名（mode/role/assistant），从响应中移除 user_id，简化 source_type，移除硬编码的联系电话
- v1.1：应用设计评审反馈 - 来源去重，澄清 422/400，mode/anchor 仅用于新对话，结构化安全枚举，统一 404 策略
- v1.0：初始设计

---

# A. 为什么使用统一的聊天界面？

## 设计理由

### 1. 共享领域模型

AI 伴侣聊天和过去的自己聊天共享基本概念：
- **Conversation（对话）**：用户与 AI 之间的聊天会话
- **Messages（消息）**：基于轮次的用户输入和 AI 响应交换
- **Context Retrieval（上下文检索）**：获取相关历史日记
- **AI Generation（AI 生成）**：使用结构化提示词调用 LLM
- **User Isolation（用户隔离）**：所有数据限定在当前用户范围内

唯一的区别是：
- **Conversation mode（对话模式）**：companion vs past_self
- **Retrieval scope（检索范围）**：可选 vs 必需（带锚点日记）
- **Prompt template（提示词模板）**：不同的系统指令
- **Tone（语气）**：温柔的伴侣 vs 反思的过去的自己

### 2. 代码可复用性

统一接口可以实现：
- 单一的 `Conversation` 和 `Message` 模型
- 单一的 `chat_service.py` 处理业务逻辑
- 单一的 `retrieval_service.py` 获取日记
- 单一的 `ai_provider.py` 调用 LLM
- 共享的前端组件（`ChatWindow`、`MessageBubble`）

### 3. 一致的用户体验

用户将"与 AI 聊天"视为一个功能，而不是两个：
- 相同的 UI 模式
- 相同的消息历史行为
- 相同的加载/错误状态
- 不同的模式只是上下文的变化

### 4. 简化测试

统一接口减少测试范围：
- 一组对话 CRUD 测试
- 一组消息存储测试
- 特定模式的测试作为变体，而非独立测试套件

### 5. 未来可扩展性

添加新的聊天模式变得简单：
- 只需添加新的 `mode` 值
- 添加提示词模板
- 添加检索策略
- 无需新端点

### 6. RESTful 对齐

```
/chat/conversations     - 对话集合
/chat/conversations/{id} - 特定对话
/chat/conversations/{id}/messages - 对话中的消息
/chat/messages          - 发送消息（创建或继续对话）
```

这遵循 REST 原则，将对话视为资源，消息视为子资源。

---

# B. 接口列表表

| HTTP 方法 | URL | 用途 | 认证 | 请求参数 | 响应字段 | 状态码 |
|-------------|-----|---------|------|-------------------|-----------------|--------------|
| **POST** | `/api/v1/chat/messages` | 发送消息，获取 AI 响应，根据需要自动创建对话 | 必需 | 见 C 节 | 见 D 节 | 200, 400, 401, 404, 422, 429, 502, 504 |
| **GET** | `/api/v1/chat/conversations` | 列出用户的对话 | 必需 | `page?`, `page_size?`, `mode?` | `conversations`, `pagination`, `total` | 200, 401, 422 |
| **POST** | `/api/v1/chat/conversations` | 显式创建新对话 | 必需 | `mode`, `title?`, `anchor_diary_id?` | `conversation`, `created_at` | 201, 400, 401, 422 |
| **GET** | `/api/v1/chat/conversations/{conversation_id}` | 获取对话元数据 | 必需 | - | `conversation` | 200, 401, 404 |
| **GET** | `/api/v1/chat/conversations/{conversation_id}/messages` | 获取对话中的消息 | 必需 | `page?`, `page_size?` | `messages`, `pagination`, `total` | 200, 401, 404, 422 |
| **DELETE** | `/api/v1/chat/conversations/{conversation_id}` | 删除对话（软删除） | 必需 | - | `deleted_conversation_id` | 200, 401, 404 |

### 端点详情

#### POST /api/v1/chat/messages
**发送消息的主要端点。** 如果未提供 `conversation_id`，则自动创建对话。

#### GET /api/v1/chat/conversations
**列出对话**，支持可选的模式过滤。支持分页。

#### POST /api/v1/chat/conversations
**显式创建对话。** 适用于预先创建对话（例如，点击"开始聊天"按钮时）。

#### GET /api/v1/chat/conversations/{conversation_id}
**获取对话元数据**（不含消息）。使用 `/conversations/{id}/messages` 获取分页消息列表。

#### GET /api/v1/chat/conversations/{conversation_id}/messages
**分页消息列表。** 用于无限滚动或加载更多历史记录。

#### DELETE /api/v1/chat/conversations/{conversation_id}
**软删除对话。** 标记为已删除，不实际删除数据。

---

# C. POST /api/v1/chat/messages - 完整请求格式

## 请求模式

```json
{
  "conversation_id": "integer | null",
  "mode": "'companion' | 'past_self' | null",
  "content": "string",
  "use_memory": "boolean",
  "anchor_diary_id": "integer | null"
}
```

## 字段规范

| 字段 | 类型 | 必需 | 默认值 | 验证 | 何时必需 |
|-------|------|----------|---------|------------|--------------|
| `conversation_id` | integer \| null | 条件 | null | 如果提供则必须存在且属于用户 | 继续对话时必需 |
| `mode` | enum \| null | 条件 | null | 必须是 'companion' 或 'past_self' | 新对话时必需（conversation_id 为 null） |
| `content` | string | 是 | - | 最少 1 字符，最多 5000 字符，已修剪 | 始终 |
| `use_memory` | boolean | 否 | false | 必须是布尔值 | 可选 |
| `anchor_diary_id` | integer \| null | 条件 | null | 如果提供则必须存在且属于用户 | mode='past_self' 且 conversation_id 为 null 时必需 |

## 字段详细说明

### conversation_id
- **用途**：继续现有对话或开始新对话
- **Null 行为**：自动创建新对话
- **验证**：
  - 如果提供：必须使用 user_id 过滤器查询（如果未找到该用户的对话则返回 404）
  - 不得被删除（`deleted_at IS NULL`）
- **何时提供**：对话中的第一条消息之后
- **何时省略**：新对话的第一条消息

### mode
- **用途**：区分业务逻辑和提示词模板
- **值**：`companion` 或 `past_self`
- **必需**：仅当 `conversation_id` 为 null（新对话）时
- **忽略**：当 `conversation_id` 被提供时（后端使用存储的 mode）
- **后端行为**：
  - 新对话：使用提供的 mode 创建对话
  - 现有对话：忽略提供的 mode，使用对话的存储 mode
- **前端决策**：
  - 首页 → `companion`
  - 记忆详情页 → `past_self`
  - 第一条消息后：不发送 mode（或发送 null）

### content
- **用途**：用户的消息文本
- **验证**（Pydantic）：
  - 修剪后最少 1 个字符
  - 最多 5000 个字符
  - 修剪前导/尾随空格
- **失败时错误**：返回 422（无法处理的实体）
- **前端**：
  - 发送前修剪
  - 显示接近限制的字符计数

### use_memory
- **用途**：启用/禁用历史日记检索
- **行为**：
  - `true`：检索相关日记作为上下文
  - `false`：不检索，AI 在没有历史记录的情况下响应
- **模式交互**：
  - `companion` + `use_memory=false`：纯伴侣聊天
  - `companion` + `use_memory=true`：带历史上下文的伴侣
  - `past_self`：始终使用记忆（字段被忽略，始终使用锚点日记）
- **默认值**：false
- **前端**：
  - 在 UI 中提供切换开关
  - 每个会话持久化偏好设置

### anchor_diary_id
- **用途**：指定以哪个日记为中心进行对话
- **必需**：当 `mode='past_self'` 且 `conversation_id` 为 null 时
- **可选**：对于继续 past_self 对话（后端使用存储的 anchor_diary_id）
- **验证**：
  - 必须使用 user_id 过滤器查询（如果未找到该用户的日记则返回 404）
  - 不得被软删除（`deleted_at IS NULL`）
- **行为**：
  - 此日记成为 AI 的主要上下文
  - 可能还会检索其他相关日记
- **前端**：
  - 用户在记忆详情页点击"与过去的自己聊天"时传递
  - 同一对话的后续消息不需要

## 按场景的请求示例

### 新伴侣对话
```json
{
  "conversation_id": null,
  "mode": "companion",
  "content": "今天感觉很累",
  "use_memory": false
}
```

### 新过去的自己对话
```json
{
  "conversation_id": null,
  "mode": "past_self",
  "content": "那天我为什么会那么难过？",
  "anchor_diary_id": 42
}
```

### 继续任何对话
```json
{
  "conversation_id": 5,
  "content": "后来我的状态有没有好一点？",
  "use_memory": true
}
```

**注意**：继续时，不需要 `mode` 和 `anchor_diary_id`（后端使用存储的值）。

## 验证规则摘要

```python
# 验证伪代码
def validate_chat_request(request, current_user):
    # Pydantic 验证（失败时返回 422）：
    # - content 长度（1-5000）
    # - mode 枚举（如果提供）
    # - use_memory 布尔值
    # - 字段类型

    # Pydantic @model_validator 中的业务规则验证（也返回 422）：
    # - 如果是新对话，mode 是必需的
    # - 如果是新的 past_self 对话，anchor_diary_id 是必需的

    # 资源存在性和所有权（返回 404）：
    # - conversation_id 必须存在且属于用户
    # - anchor_diary_id 必须存在且属于用户

    return True
```

**重要**：所有字段验证（包括关于必需字段的业务规则）都返回 422。这是标准的 FastAPI/Pydantic 行为。

## 状态码策略

| 代码 | 用途 | 示例 |
|------|-------|----------|
| **422** | 所有验证失败 | 空内容、内容 > 5000 字符、无效枚举、错误类型、缺少必需字段 |
| **400** | 保留供将来使用 | v1 中未使用（所有验证返回 422） |
| **404** | 资源未找到或访问被拒绝 | conversation_id 未找到或属于另一用户、日记未找到或属于另一用户 |

---

# D. POST /api/v1/chat/messages - 完整响应格式

## 响应模式

```json
{
  "success": true,
  "data": {
    "conversation": { ... },
    "user_message": { ... },
    "assistant_message": { ... },
    "retrieval": { ... },
    "sources": [ ... ],  // 单一真实来源
    "safety": { ... },
    "created_at": "..."
  },
  "message": "message_sent",
  "request_id": "req_abc123"
}
```

## 字段规范

### conversation
对话对象（已创建或更新）。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `id` | integer | 对话 ID |
| `mode` | string | 'companion' 或 'past_self' |
| `title` | string \| null | 自动生成或用户提供 |
| `anchor_diary_id` | integer \| null | 用于 past_self 模式 |
| `started_at` | datetime ISO 8601 | 对话开始时间 |
| `updated_at` | datetime ISO 8601 | 最后消息时间 |
| `message_count` | integer | 对话中的总消息数 |

**注意**：`user_id` 不在响应中返回 - 仅存在于数据库和后端认证上下文中。

### user_message
刚刚发送的消息（现已持久化）。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `id` | integer | 消息 ID |
| `conversation_id` | integer | 所属对话 |
| `role` | 'user' | 对此字段始终为 'user' |
| `content` | string | 用户的消息文本 |
| `created_at` | datetime ISO 8601 | 消息创建时间 |

**注意**：从消息中移除了 `sources` - 顶层单一真实来源。

### assistant_message
AI 的响应消息。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `id` | integer | 消息 ID |
| `conversation_id` | integer | 所属对话 |
| `role` | 'assistant' | 对此字段始终为 'assistant' |
| `content` | string | AI 的响应文本 |
| `created_at` | datetime ISO 8601 | 消息创建时间 |

**注意**：从消息中移除了 `sources` - 顶层单一真实来源。

### sources（顶层）
生成此响应时使用的参考日记的**单一真实来源**。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `diary_id` | integer | 日记 ID |
| `diary_date` | date ISO 8601 | 日记撰写时间 |
| `title` | string | 日记标题 |
| `excerpt` | string | 内容的前 100 字符 |
| `emotion_label` | string | 主要情绪 |
| `relevance_score` | float | 0.0 到 1.0，相关性置信度 |
| `source_type` | string | `anchor` 或 `retrieved` |

**注意**：具体检索算法细节在 `retrieval.strategy` 中，不在每个来源中重复。

### retrieval
关于如何检索历史上下文的元数据。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `used` | boolean | 是否尝试了检索 |
| `strategy` | string | 使用了哪种检索策略（如 "none"、"keyword_emotion_time"） |
| `total_found` | integer | 找到的匹配日记总数 |
| `used_in_context` | integer | 有多少被发送到 AI |

**注意**：内部查询重写/处理不暴露 - 仅策略名称和计数。

### safety
内容安全检查结果，带有**结构化枚举**。

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `flagged` | boolean | 内容是否被标记 |
| `level` | enum | `none`、`low`、`medium`、`high` |
| `category` | enum \| null | `emotional_distress`、`self_harm_risk`、`violence_risk`、`null` |
| `action` | enum | `none`、`show_notice`、`suggest_support`、`trigger_emergency_flow` |

**注意**：使用 `assistant_message.created_at` 作为响应时间戳。没有重复的顶层 `created_at`。

---

# E. 伴侣模式 - 请求/响应示例

## 示例 1：新对话，无记忆

### 请求
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

### 响应
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

## 示例 2：继续对话，使用记忆

### 请求
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": 1,
  "content": "我最近好像总是容易焦虑",
  "use_memory": true
}
```

**注意**：未提供 `mode` - 后端使用存储的对话模式。

### 响应
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

# F. 过去的自己模式 - 请求/响应示例

## 示例：新过去的自己对话

### 请求
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

### 响应
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

## 示例：继续过去的自己对话

### 请求
```json
POST /api/v1/chat/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "conversation_id": 5,
  "content": "后来我的状态有没有好一点？",
  "use_memory": true
}
```

**注意**：不需要 `mode` 或 `anchor_diary_id` - 后端使用存储的对话值。

### 响应
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

# G. 无检索结果 - 响应示例

## 示例：用户无日记历史

### 请求
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

### 响应
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

# H. 模型调用失败 - 响应策略

## 失败处理策略

**重要**：v1 不使用带有 `success=true` 的回退消息。模型失败返回真实错误代码。

### 1. 超时（504）

**场景**：AI provider 响应时间过长

**行为**：
- 用户消息已保存
- 未创建 assistant 消息
- 返回 504 错误
- 前端显示"生成失败"并提供重试选项
- 可以通过使用相同的 conversation_id 再次发送来重试消息

**响应**：
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

### 2. Provider 错误（502）

**场景**：AI provider 返回 5xx 错误

**行为**：
- 用户消息已保存
- 未创建 assistant 消息
- 返回 502 错误
- 前端显示"服务不可用"并提供重试选项
- 记录日志以供监控

**响应**：
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

### 3. 速率限制（429）

**场景**：达到 AI provider 速率限制

**响应**：
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

**行为**：
- 返回 429 状态码
- 包含 `retry_after`（秒）
- 前端应显示倒计时
- 用户可等待后重试

### 4. 内容安全标记

**场景**：用户输入触发安全关注

**响应**：
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

**行为**：
- 仍然响应，但使用特定的关怀消息
- 在 `safety` 对象中标记，使用结构化枚举
- 不提供诊断或治疗
- 支持资源由配置驱动（不在响应中硬编码）
- 前端根据 `safety.action` 显示资源

---

# I. 错误响应设计

## 错误响应格式

所有错误响应遵循此格式（来自 `schemas/common.py`）：

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

## 状态码策略

| 状态码 | 用途 | 示例 |
|-------------|-------|----------|
| **422** | 所有验证失败 | 空内容、内容 > 5000 字符、无效枚举、错误字段类型、缺少必需字段（mode、anchor_diary_id） |
| **400** | 保留供将来使用 | v1 中未使用 - 所有验证都是 422 |
| **404** | 资源未找到或访问被拒绝 | 统一策略 - 从不揭示资源是否属于另一用户 |
| **401** | 认证失败 | 无效或缺失的 JWT token |
| **429** | 速率限制 | 每分钟消息过多 |
| **502/504** | AI 服务失败 | Provider 错误或超时 |

## 完整错误情况

### 422 无法处理的实体 - 验证失败

**Pydantic 自动返回 422 当**：
- 修剪后内容为空
- 内容超过 5000 字符
- 无效的 mode 值（非 'companion' 或 'past_self'）
- 错误的字段类型（如 content 为数字）
- **@model_validator 中的业务规则违规**：
  - 新对话缺少 mode
  - 新的 past_self 对话缺少 anchor_diary_id

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

**注意**：在 FastAPI/Pydantic 中，在 `@model_validator` 中引发的 `ValueError` 也返回 422，而非 400。这是标准行为。

### 400 错误请求 - 保留供将来使用

**v1 中未使用**。所有验证（包括业务规则）都返回 422。

保留给潜在的将来用例，如：
- 资源之间的冲突
- 基于状态的业务违规
- 其他非验证错误

### 401 未授权 - 未登录

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

**场景**：无 JWT token 或无效 token

**行为**：前端应重定向到登录页

### 404 未找到 - 统一策略（资源未找到或访问被拒绝）

**安全原则**：始终返回 404，从不返回 403

**理由**：不揭示资源是否存在或属于另一用户。这可防止：
- 用户枚举攻击
- 信息泄漏（关于哪些资源存在）
- 对有效对话/日记 ID 的"钓鱼"

**实现**：
```python
# 所有资源查询都包含 user_id 过滤器
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,  # <-- 始终按用户过滤
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # 返回 404，无论是：
    # - 对话不存在，或
    # - 对话存在但属于另一用户，或
    # - 对话已被删除
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

**应用于**：
- 对话访问（通过 conversation_id）
- 锚点日记访问（通过 anchor_diary_id）
- 任何用户范围的资源

### 429 请求过多 - 速率限制

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

**场景**：用户在短时间内发送过多消息

**行为**：前端应显示倒计时并禁用发送按钮

### 502 网关错误 - 模型服务失败

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

**场景**：AI provider 返回 5xx 错误

**注意**：在生产环境中，这应触发回退响应而非硬错误

### 504 网关超时 - 模型调用超时

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

**场景**：AI provider 响应时间过长

**注意**：在生产环境中，这应触发回退响应而非硬错误

---

# J. Pydantic 模式设计预览

## 模式层次结构

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

## 模式定义

### MessageSource
```python
class MessageSource(BaseModel):
    """新消息响应的来源日记（无快照字段）"""
    diary_id: int
    diary_date: date
    title: str
    excerpt: str  # 前 100 个字符
    emotion_label: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_type: Literal["anchor", "retrieved"]
```

**注意**：仅用于 `ChatResponse` 的即时响应。对于历史来源，使用 `MessageSourceRead`。

### RetrievalMetadata
```python
class RetrievalMetadata(BaseModel):
    """关于如何检索上下文的信息"""
    used: bool
    strategy: str
    total_found: int = Field(ge=0)
    used_in_context: int = Field(ge=0)
```

### SafetyCheck（带结构化枚举）
```python
class SafetyCheck(BaseModel):
    """带结构化枚举的内容安全检查结果"""
    flagged: bool
    level: Literal["none", "low", "medium", "high"]
    category: Literal["emotional_distress", "self_harm_risk", "violence_risk"] | None
    action: Literal["none", "show_notice", "suggest_support", "trigger_emergency_flow"]
```

### MessageRead
```python
class MessageRead(BaseModel):
    """在单个消息上下文中返回的消息"""
    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
```

**注意**：不带来源的基本消息表示。使用 `ChatHistoryItem` 获取带来源的消息列表。

### MessageSourceRead
```python
class MessageSourceRead(BaseModel):
    """消息的来源日记（来自 message_sources 表）"""
    id: int
    diary_id: int | None  # 如果日记被删除则为 NULL
    source_type: Literal["anchor", "retrieved"]
    # 快照字段 - 即使日记删除后也保留
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
    """对话历史中的消息，带可选来源"""
    message: MessageRead
    sources: list[MessageSourceRead]  # 用户消息为空数组
```

**设计说明**：
- `sources` 包含在历史项级别，而非 `MessageRead` 中
- 用户消息有空的 `sources` 数组
- Assistant 消息包含来自 `message_sources` 表的所有来源
- 快照字段即使在原始日记删除后也能保存来源显示
- `diary_id` 在删除后可能为 NULL，但快照保持完整

### ConversationRead
```python
class ConversationRead(BaseModel):
    """返回给前端的对话"""
    id: int
    mode: Literal["companion", "past_self"]
    title: str | None
    anchor_diary_id: int | None
    started_at: datetime
    updated_at: datetime
    message_count: int = Field(ge=0)
```

**注意**：不返回 `user_id` - 仅存在于数据库和后端认证上下文中。

### ChatRequest
```python
class ChatRequest(BaseModel):
    """POST /api/v1/chat/messages 的请求"""
    conversation_id: int | None = None
    mode: Literal["companion", "past_self"] | None = None
    content: str = Field(min_length=1, max_length=5000)
    use_memory: bool = False
    anchor_diary_id: int | None = None

    @model_validator(mode="after")
    def validate_business_rules(self) -> "ChatRequest":
        # 业务规则：新对话需要 mode
        if self.conversation_id is None and self.mode is None:
            raise ValueError("mode required for new conversation")

        # 业务规则：past_self 需要 anchor_diary_id
        if self.mode == "past_self" and self.anchor_diary_id is None:
            raise ValueError("anchor_diary_id required for past_self mode")

        return self
```

**注意**：`@model_validator` 中的业务规则验证引发 `ValueError`，FastAPI/Pydantic 将其转换为 **422**，而非 400。这是标准行为。

### ChatResponse
```python
class ChatResponse(BaseModel):
    """POST /api/v1/chat/messages 的响应"""
    conversation: ConversationRead
    user_message: MessageRead
    assistant_message: MessageRead
    retrieval: RetrievalMetadata
    sources: list[MessageSource]  # 单一真实来源
    safety: SafetyCheck
```

**注意**：没有顶层 `created_at` - 使用 `assistant_message.created_at`。v1 中没有 `fallback` 字段。

### ConversationCreate
```python
class ConversationCreate(BaseModel):
    """POST /api/v1/chat/conversations 的请求"""
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
    """GET /api/v1/chat/conversations 的响应"""
    conversations: list[ConversationRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
```

### ConversationDetailResponse
```python
class ConversationDetailResponse(BaseModel):
    """GET /api/v1/chat/conversations/{id} 的响应"""
    conversation: ConversationRead
```

### MessageListResponse
```python
class MessageListResponse(BaseModel):
    """GET /api/v1/chat/conversations/{id}/messages 的响应"""
    messages: list[ChatHistoryItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
```

**设计说明**：
- 返回带消息 + 来源的 `ChatHistoryItem` 数组
- 用户消息有空的 `sources` 数组
- Assistant 消息包含来自 `message_sources` 表的所有来源
- 支持分页以实现无限滚动
- `page` 从 1 开始索引

---

# K. 前端 TypeScript 类型设计预览

## 类型层次结构

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

## 类型定义

### MessageSource
```typescript
export interface MessageSource {
  diary_id: number;
  diary_date: string;  // ISO 8601 日期字符串
  title: string;
  excerpt: string;
  emotion_label: string;
  relevance_score: number;  // 0.0 到 1.0
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

### SafetyCheck（带结构化枚举）
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
  diary_id: number | null;  // 如果日记被删除则为 NULL
  source_type: 'anchor' | 'retrieved';
  // 快照字段 - 即使日记删除后也保留
  diary_date_snapshot: string | null;  // ISO 8601 日期字符串或 null
  title_snapshot: string;
  excerpt_snapshot: string;
  emotion_label_snapshot: string | null;
  relevance_score: number;  // 0.0 到 1.0
  rank: number;  // >= 1
}
```

**注意**：用于 `ChatHistoryItem` 以获取历史消息，保留快照数据。

### ChatMessage
```typescript
export interface ChatMessage {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;  // ISO 8601 日期时间字符串
}
```

**注意**：不带来源的基本消息类型。使用 `ChatHistoryItem` 获取带来源的消息列表。

### ChatHistoryItem
```typescript
export interface ChatHistoryItem {
  message: ChatMessage;
  sources: MessageSourceRead[];  // 用户消息为空数组
}
```

**设计说明**：
- `sources` 包含在历史项级别
- 用户消息有空的 `sources` 数组
- Assistant 消息包含来自数据库的所有来源
- 快照字段确保即使在日记删除后来源也可显示
- `diary_id` 在删除后可能为 null，但快照持久存在

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

**注意**：不返回 `user_id` - 仅存在于数据库和后端认证上下文中。

### ChatRequest
```typescript
export interface ChatRequest {
  conversation_id?: number | null;
  mode?: 'companion' | 'past_self' | null;  // 新对话时必需
  content: string;
  use_memory?: boolean;
  anchor_diary_id?: number | null;  // past_self + 新对话时必需
}
```

### ChatResponse
```typescript
export interface ChatResponse {
  conversation: ChatConversation;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  retrieval: RetrievalMetadata;
  sources: MessageSource[];  // 单一真实来源
  safety: SafetyCheck;
}
```

**注意**：使用 `assistant_message.created_at` 作为响应时间戳。v1 中没有 `fallback` 字段。

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
  page_size: number;  // 1 到 100
  total: number;  // >= 0
}
```

### API 响应包装器
```typescript
// 已在 types/index.ts 中，为 chat 重用
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  request_id: string;
}

// 使用
export type ChatApiResponse = ApiResponse<ChatResponse>;
export type ConversationListApiResponse = ApiResponse<ConversationListResponse>;
export type ConversationDetailApiResponse = ApiResponse<ConversationDetailResponse>;
export type MessageListApiResponse = ApiResponse<MessageListResponse>;
```

### 前端使用示例

```typescript
// 第一条消息（新伴侣对话）
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'companion',  // 新对话时必需
    content: '今天感觉很累',
    use_memory: false
  })
});
const conversationId = response.data.conversation.id;

// 继续对话（不需要 mode）
const response2 = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: conversationId,
    content: '我最近好像总是焦虑',
    use_memory: true
  })
});

// 新的 past_self 对话
const response3 = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'past_self',
    anchor_diary_id: diaryId,  // past_self 时必需
    content: '那天我为什么会那么难过？'
  })
});

// 处理安全标记
if (response.data.safety.flagged) {
  switch (response.data.safety.action) {
    case 'show_notice':
      // 显示信息通知
      break;
    case 'suggest_support':
      // 从后端配置获取支持资源
      // 不在前端硬编码
      const resources = await fetchSupportResources();
      showSupportResources(resources);
      break;
    case 'trigger_emergency_flow':
      // 从后端配置获取紧急联系人
      // 不在前端硬编码
      const contacts = await fetchEmergencyContacts();
      showEmergencyContacts(contacts);
      break;
  }
}
```

---

# L. 权限约束

## 用户 ID 隔离

### 所有请求必须
1. 在 `Authorization: Bearer` 头中包含有效的 JWT token
2. Token 被解码以从 `sub` 声明获取 `user_id`
3. 从数据库获取用户对象以验证活动状态

### 后端强制执行
```python
# 所有 chat 端点都使用此依赖
@router.post("/chat/messages")
async def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_user),  # <-- 强制认证
    db: Session = Depends(get_db)
):
    # 所有查询都自动按 user.id 过滤
    pass
```

### 禁止字段
- ❌ 前端不得在请求体中发送 `user_id`
- ❌ 前端不得在查询参数中发送 `user_id`
- ❌ 后端不得信任请求中存在的 `user_id`（如果存在）

## 资源所有权验证 - 统一 404 策略

### 安全原则
**对于用户范围的资源始终返回 404，从不返回 403**。

这可防止：
- 用户枚举（测试有效 ID）
- 信息泄漏（揭示哪些资源存在）
- "钓鱼"攻击（猜测对话/日记 ID）

### 实现模式
```python
# 错误：返回 403，揭示资源存在
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id
).first()
if conversation and conversation.user_id != user.id:
    raise HTTPException(status_code=403)  # 不要这样做

# 正确：返回 404，不揭示任何信息
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == user.id,  # <-- 始终按用户过滤
    Conversation.deleted_at.is_(None)
).first()
if conversation is None:
    raise HTTPException(status_code=404)  # 统一 404
```

### 应用于所有用户范围的资源

#### 对话访问
```python
# 单个查询带用户过滤器
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # 返回 404，无论是：
    # - 对话不存在，或
    # - 对话存在但属于另一用户，或
    # - 对话已被删除
    raise HTTPException(status_code=404, detail="conversation_not_found")
```

#### 日记访问（用于 anchor_diary_id）
```python
# 单个查询带用户过滤器
diary = db.query(Diary).filter(
    Diary.id == anchor_diary_id,
    Diary.user_id == current_user.id,  # <-- 用户过滤器
    Diary.deleted_at.is_(None)
).first()

if diary is None:
    # 返回 404，无论是：
    # - 日记不存在，或
    # - 日记存在但属于另一用户，或
    # - 日记已被删除
    raise HTTPException(status_code=404, detail="diary_not_found")
```

#### 检索结果过滤
```python
# 所有检索查询都包含用户过滤器
def retrieve_context(user_id: int, query: str):
    results = db.query(Diary).join(EmotionAnalysis).filter(
        Diary.user_id == user_id,  # <-- 始终按用户过滤
        Diary.deleted_at.is_(None),
        # ... 其他过滤器
    ).all()
    return results
```

#### 消息来源验证
```python
# 来源已通过检索查询过滤
# 双重检查是防御性编程
validated_sources = []
for source in raw_sources:
    # 如果检索正确，这应该始终通过
    diary = db.query(Diary).filter(
        Diary.id == source.diary_id,
        Diary.user_id == current_user.id  # <-- 验证所有权
    ).first()
    if diary:
        validated_sources.append(source)

return validated_sources
```

## 架构保证

1. **JWT 验证**：Token 必须有效且未过期
2. **用户查找**：用户必须存在且具有 `status='active'`
3. **查询过滤**：所有数据库查询都包含 `user_id` 过滤器
4. **统一 404**：从不揭示资源是否存在或属于另一用户

### 数据库级安全
```sql
-- 所有用户范围的查询都遵循此模式
SELECT * FROM conversations
WHERE user_id = ? AND id = ? AND deleted_at IS NULL;

-- 外键确保引用完整性
-- ON DELETE CASCADE 防止孤立记录
```

### 审计日志（推荐）
```python
# 记录所有资源访问尝试
conversation = db.query(Conversation).filter(
    Conversation.id == conversation_id,
    Conversation.user_id == current_user.id,
    Conversation.deleted_at.is_(None)
).first()

if conversation is None:
    # 记录访问尝试（无论是钓鱼还是 genuine 错误）
    logger.info(
        "Conversation access failed",
        user_id=current_user.id,
        target_conversation=conversation_id
    )
    raise HTTPException(status_code=404, detail="conversation_not_found")
```

---

# M. 幂等性和重复提交处理

## 幂等性考虑

### POST /api/v1/chat/messages 不是幂等的

**原因**：每次调用都会创建新消息（并可能创建对话）。

**行为**：
- 相同的请求发送两次 → 创建两条消息
- 这对于聊天是有意的（用户可能真的想重复自己）

### 重复提交预防（UI 级别）

#### 前端策略
```typescript
// 在 ChatWindow 组件中
const [isSending, setIsSending] = useState(false);

async function handleSend() {
  if (isSending) return;  // 防止重复提交

  setIsSending(true);

  try {
    await sendChatMessage(request);
  } finally {
    setIsSending(false);
  }
}
```

#### 后端策略（可选的幂等性密钥）
```python
# 可选：为关键场景添加幂等性密钥
class ChatRequest(BaseModel):
    idempotency_key: str | None = None  # 来自客户端的可选 UUID
    # ... 其他字段

# 在服务层
if request.idempotency_key:
    existing = db.query(Message).filter(
        Message.idempotency_key == request.idempotency_key
    ).first()
    if existing:
        return previous_response  # 返回缓存的响应
```

**推荐**：v1 不需要。UI 级别的预防就足够了。

### 对话标题生成

**策略**：基于模式和第一条消息/锚点日记确定性地生成

```python
def generate_conversation_title(mode: str, first_message: str, anchor_diary: Diary | None) -> str:
    if mode == "past_self" and anchor_diary:
        return f"回忆：{anchor_diary.diary_date} 的记忆"
    else:
        # 截断第一条消息
        return first_message[:30] + "..." if len(first_message) > 30 else first_message
```

**结果**：相同输入 → 相同标题（确定性）

---

# N. 流式响应 - v1 应该包含吗？

## 建议：v1 不包含流式

### 反对 v1 流式的理由

#### 1. 复杂性 vs 收益
- **流式需要**：
  - WebSocket 或 Server-Sent Events（SSE）
  - 不同的客户端处理（渐进式渲染）
  - 错误处理复杂性（部分失败）
  - 状态管理复杂性

- **v1 优先级**：首先让基本聊天可靠地工作
- **流式收益**：对于长 AI 响应更好的 UX
- **权衡**：对于初始版本不值得这种复杂性

#### 2. 当前项目约束
根据设计文档：
- "第一版不引入 WebSocket"
- "第一版不引入复杂技术"
- 专注于稳定性和课程演示

#### 3. AI 响应特征
- Companion/Past Self 响应通常较短（100-300 tokens）
- 不需要复杂的思维链
- 没有代码生成或长篇内容
- 标准请求/响应就足够了

#### 4. 前端简单性
```typescript
// 不带流式（v1）
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify(request)
});
// 立即显示消息

// 带流式（未来）
const response = await fetch('/chat/messages/stream', { ... });
const reader = response.body.getReader();
// 渐进式渲染，复杂状态
```

#### 5. 回退处理
不带流式：
- 超时时容易回退到预定义消息
- 清晰的成功/失败状态

带流式：
- 部分响应然后超时 = 令人困惑的 UX
- 需要处理"停滞的流"

### 何时添加流式（v2+）

当以下情况时考虑流式：
1. v1 稳定并经过用户测试
2. 需要更长的响应（如反思摘要）
3. 用户反馈表明需要流式
4. 团队有能力正确实施

### v1 推荐方法

**带加载状态的标准 REST**：

```typescript
// 前端
const [isLoading, setIsLoading] = useState(false);

async function handleSend() {
  setIsLoading(true);
  try {
    const response = await sendChatMessage(request);
    // 立即显示消息
  } finally {
    setIsLoading(false);
  }
}
```

```python
# 后端
@router.post("/chat/messages")
async def send_message(...):
    # 完整生成（最多 30 秒超时）
    # 返回完整响应
    pass
```

**长等待时间的回退**：
- 显示"AI 正在思考..."指示器
- 如果超时，使用回退消息
- 用户体验：短暂等待，然后完整消息

### 结论

**v1**：标准请求/响应（无流式）
**v2+**：如果用户测试表明需要，考虑 SSE 或 WebSocket

---

# 总结

此 API 设计提供：

1. **统一接口**，用于两种聊天模式，模式区分清晰
2. **单一真实来源**，用于来源（从消息中移除重复）
3. **清晰的状态码策略**：422 用于所有验证，404 用于所有访问问题，502/504 用于 AI 失败
4. **简化的继续对话**：只需要 conversation_id 和 content
5. **结构化安全枚举**：使用 `action` 字段进行稳定的前端处理
6. **统一 404 策略**：从不揭示资源是否存在或属于另一用户
7. **完整的请求/响应契约**，指定所有字段
8. **全面的错误处理**，涵盖所有边界情况
9. **强大的权限模型**，在多个级别强制执行
10. **务实的流式决策**（推迟到 v2）
11. **清晰的类型定义**，用于后端和前端
12. **AI 失败的真实错误代码**：502/504，用户消息已保存，无假的回退消息
13. **透明度**，关于检索和使用了什么数据
14. **标准化的字段命名**：全程使用 mode/role/assistant
15. **配置驱动的支持资源**：无硬编码的联系电话

该设计尊重所有现有的项目架构约束，同时为 RAG 记忆聊天功能提供了坚实的基础。

---

# 附录：集成点

## 前端使用示例

### 开始伴侣聊天
```typescript
// 第一条消息（新对话）
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: null,
    mode: 'companion',
    content: '今天感觉很累',
    use_memory: false
  })
});

// 保存 conversation_id 用于后续消息
const conversationId = response.data.conversation.id;
```

### 继续聊天
```typescript
// 后续消息 - 不需要 mode
const response = await apiRequest<ChatResponse>('/chat/messages', {
  method: 'POST',
  body: JSON.stringify({
    conversation_id: conversationId,
    content: '我最近好像总是焦虑',
    use_memory: true
  })
});
```

### 开始过去的自己聊天
```typescript
// 从 MemoryDetailPage，当用户点击"与过去的自己聊天"时
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

### 处理安全标记
```typescript
const response = await sendChatMessage(request);

if (response.data.safety.flagged) {
  switch (response.data.safety.action) {
    case 'show_notice':
      showNotice('This conversation has been flagged for review.');
      break;
    case 'suggest_support':
      // 从后端配置获取支持资源
      // 不在前端硬编码
      const resources = await fetchSupportResources();
      showSupportResources(resources);
      break;
    case 'trigger_emergency_flow':
      // 从后端配置获取紧急联系人
      // 不在前端硬编码
      const contacts = await fetchEmergencyContacts();
      showEmergencyContacts(contacts);
      break;
  }
}
```

**重要**：支持资源和紧急联系人是配置驱动的，从后端获取。不要在前端硬编码电话号码或 URL。

### 列出对话
```typescript
// 在聊天历史页
const response = await apiRequest<ConversationListResponse>('/chat/conversations', {
  method: 'GET',
  params: { page: 1, page_size: 20, mode: 'companion' }
});
```

---

# 设计批准后的后续步骤

1. **后端实现**
   - 创建 `models/chat.py`，包含 Conversation 和 Message
   - 创建 `schemas/chat.py`，包含所有 Pydantic 模式
   - 创建 `services/chat_service.py`，包含业务逻辑
   - 创建 `services/retrieval_service.py`，包含日记检索
   - 创建 `routers/chat.py`，包含所有端点
   - 在 `tests/test_chat.py` 中添加测试

2. **前端实现**
   - 创建 `types/chat.ts`，包含 TypeScript 类型
   - 创建 `api/chat.ts`，包含 API 客户端函数
   - 增强 `ChatPage`，实现真实的消息持久化
   - 增强 `MemoryDetailPage`，实现过去的自己聊天
   - 创建 `ChatWindow` 和 `MessageBubble` 组件

3. **测试**
   - 所有端点的后端单元测试
   - 对话流程的后端集成测试
   - 前端组件测试
   - 端到端用户流程测试

4. **文档**
   - 更新 API 文档
   - 更新用户故事
   - 创建演示脚本用于答辩

---

# API 契约冻结检查表

此检查表确认 API 设计已冻结并准备好实现。

## ✅ 路径已固定

- [x] `POST /api/v1/chat/messages` - 发送消息
- [x] `GET /api/v1/chat/conversations` - 列出对话
- [x] `POST /api/v1/chat/conversations` - 创建对话
- [x] `GET /api/v1/chat/conversations/{id}` - 获取对话元数据
- [x] `GET /api/v1/chat/conversations/{id}/messages` - 获取消息（分页）
- [x] `DELETE /api/v1/chat/conversations/{id}` - 删除对话

## ✅ 字段名已固定

### 请求字段
- [x] `conversation_id: integer | null`
- [x] `mode: "companion" | "past_self" | null`
- [x] `content: string`
- [x] `use_memory: boolean`
- [x] `anchor_diary_id: integer | null`

### 响应字段
- [x] `conversation.mode`（非 `conversation_type`）
- [x] `message.role`（非 `sender`）
- [x] `role: "user" | "assistant"`（非 `"user" | "ai"`）
- [x] `retrieval.used: boolean`
- [x] `retrieval.strategy: string`
- [x] `retrieval.total_found: integer`
- [x] `retrieval.used_in_context: integer`
- [x] `source.source_type: "anchor" | "retrieved"`

### 排除字段
- [x] `user_id` 从所有响应中移除（仅存在于数据库和认证上下文中）
- [x] 顶层 `created_at` 移除（使用 `assistant_message.created_at`）
- [x] `retrieval.query` 移除（内部查询不暴露）
- [x] `fallback`、`fallback_reason` 移除（v1 使用真实错误代码）

## ✅ 枚举已固定

### 模式枚举
- [x] `"companion"`
- [x] `"past_self"`

### 角色枚举
- [x] `"user"`
- [x] `"assistant"`

### 来源类型枚举
- [x] `"anchor"`
- [x] `"retrieved"`

### 安全级别枚举
- [x] `"none"`
- [x] `"low"`
- [x] `"medium"`
- [x] `"high"`

### 安全类别枚举
- [x] `"emotional_distress"`
- [x] `"self_harm_risk"`
- [x] `"violence_risk"`
- [x] `null`

### 安全操作枚举
- [x] `"none"`
- [x] `"show_notice"`
- [x] `"suggest_support"`
- [x] `"trigger_emergency_flow"`

## ✅ 状态码已固定

### 成功代码
- [x] `200 OK` - POST /api/v1/chat/messages（所有情况）
- [x] `200 OK` - GET /api/v1/chat/conversations
- [x] `201 Created` - POST /api/v1/chat/conversations

### 错误代码
- [x] `401 Unauthorized` - 认证失败
- [x] `404 Not Found` - 资源未找到或访问被拒绝（统一策略）
- [x] `422 Unprocessable Entity` - 所有验证失败（包括 @model_validator 中的业务规则）
- [x] `429 Too Many Requests` - 速率限制
- [x] `502 Bad Gateway` - AI provider 错误
- [x] `504 Gateway Timeout` - AI 超时

### 保留代码
- [x] `400 Bad Request` - 保留供将来使用（v1 中未使用）

## ✅ 权限策略已固定

- [x] 所有请求都需要有效的 JWT token
- [x] 用户 ID 来自 token `sub` 声明
- [x] 所有数据库查询都按 `user_id` 过滤
- [x] 统一 404 策略（从不 403，从不揭示存在性）
- [x] `user_id` 不在任何响应中返回

## ✅ AI 失败策略已固定

- [x] 超时：保存用户消息，返回 504，不创建 assistant 消息
- [x] Provider 错误：保存用户消息，返回 502，不创建 assistant 消息
- [x] 无 `success=true` 带回退消息
- [x] 前端显示失败并允许重试
- [x] 无假的 assistant 消息污染聊天历史

## ✅ v1 范围已固定

- [x] 无流式（推迟到 v2）
- [x] 仅标准请求/响应
- [x] 真实错误代码（无 success=true 回退）
- [x] 配置驱动的支持资源（无硬编码联系人）

## ✅ 同步点

### API 契约的任何未来更改都必须更新所有：
1. [x] 后端 Pydantic 模式（`backend/app/schemas/chat.py`）
2. [x] 前端 TypeScript 类型（`frontend/src/types/chat.ts`）
3. [x] 本设计文档（`docs/vibe-logs/log-07-rag-chat-api-design.md`）
4. [x] API 测试（后端和前端）
5. [x] 使用 API 的组件实现

---

## API 契约状态：**已冻结**

此 API 设计现已冻结。实现应完全按照指定进行。契约的任何更改需要：
1. 更新此检查表
2. 更新所有同步点
3. 团队评审和批准
4. 版本递增（v1.2 → v1.3）
