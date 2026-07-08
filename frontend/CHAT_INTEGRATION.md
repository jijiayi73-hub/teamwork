# Frontend Chat Integration

本目录包含为聊天功能准备的前端代码。

## 状态说明

**当前状态**: 后端聊天API尚未实现

这些文件是为将来后端API实现后准备的。在后端API实现之前，这些函数调用会返回404错误。

## 新增文件

### 1. TypeScript 类型定义
`src/types/chat.ts` - 聊天功能的TypeScript类型定义

包含类型：
- `ConversationMode`: 对话模式 ('companion' | 'past_self')
- `MessageRole`: 消息角色 ('user' | 'assistant')
- `MessageStatus`: 消息状态 ('pending' | 'completed' | 'failed')
- `SourceType`: 来源类型 ('anchor' | 'retrieved')
- `Conversation`: 对话实体
- `Message`: 消息实体
- `MessageSource`: 消息来源实体
- 各种请求/响应类型

### 2. Chat API 客户端 (TypeScript)
`src/api/chat.ts` - TypeScript版本的聊天API客户端

提供函数：
- `createConversation()` - 创建新对话
- `listConversations()` - 获取对话列表
- `getConversation()` - 获取单个对话
- `listMessages()` - 获取消息列表
- `sendMessage()` - 发送消息
- `deleteConversation()` - 删除对话

### 3. Chat API 函数 (JavaScript - 已集成)
`src/api/client.js` - 更新了聊天API函数（JavaScript版本）

新增导出：
- `createConversation`
- `listConversations`
- `getConversation`
- `listMessages`
- `sendMessage`
- `deleteConversation`

### 4. 示例组件
`src/components/ChatPageExample.jsx` - 使用新聊天API的示例组件

功能：
- 对话列表展示
- 创建新对话
- 选择对话查看消息
- 发送消息
- 显示消息来源（日记引用）
- 删除对话

## API 端点（待后端实现）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/chat/conversations` | POST | 创建对话 |
| `/api/v1/chat/conversations` | GET | 获取对话列表 |
| `/api/v1/chat/conversations/{id}` | GET | 获取对话详情 |
| `/api/v1/chat/conversations/{id}/messages` | GET | 获取消息列表 |
| `/api/v1/chat/messages` | POST | 发送消息 |
| `/api/v1/chat/conversations/{id}` | DELETE | 删除对话 |

## 使用方法

### 当后端API就绪后：

1. **替换 ChatPage**:
   在 `App.jsx` 中：
   ```jsx
   // 替换
   import { ChatPageExample } from './components/ChatPageExample';
   // 使用
   {route.name === 'chat' && <ChatPageExample />}
   ```

2. **或者逐步集成**:
   将 `ChatPageExample.jsx` 中的功能逐步集成到现有的 `ChatPage` 组件中。

### 当前可用功能

目前聊天功能仍然使用 `/api/v1/entries` 端点（原有实现）。新API需要等待后端实现后才能使用。

## 数据库Schema对应

前端类型与以下数据库表对应：
- `conversations` 表 → `Conversation` 类型
- `messages` 表 → `Message` 类型
- `message_sources` 表 → `MessageSource` 类型

## 注意事项

1. **后端依赖**: 这些功能需要后端实现相应的API端点
2. **认证**: 所有API调用都需要JWT token
3. **错误处理**: API函数会抛出错误，需要try/catch处理
4. **TypeScript可选**: 项目当前使用JSX，TypeScript文件供类型参考

## 下一步

等待后端实现：
1. `backend/app/schemas/chat.py`
2. `backend/app/services/chat_service.py`
3. `backend/app/routers/chat.py`

后端API就绪后，前端可以立即开始使用这些新功能。
