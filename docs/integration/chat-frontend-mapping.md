# Chat Frontend Mapping

本文件只说明 Chat API 数据如何进入页面状态；字段定义以 `docs/contracts/chat-api-v1.md` 和 `/openapi.json` 为准。

## 接口到页面状态

| 后端字段/状态 | 前端行为 |
| --- | --- |
| `data.assistant_message.content` | 放入现有 AI 消息气泡 |
| `data.assistant_message.role="assistant"` | 渲染为 assistant 侧消息 |
| `data.user_message.role="user"` | 渲染为 user 侧消息 |
| `data.conversation.id` | 保存为当前 `conversationId` |
| `data.conversation.mode` | 保存当前聊天模式 |
| `data.conversation.anchor_diary_id` | Past Self 对话保存 anchor 关联 |
| `data.sources` | 当前版本保存但暂不展示 |
| `data.retrieval` | 当前版本保存为调试/诊断状态 |
| `data.safety.action="show_notice"` | 进入已有提示状态 |
| 请求进行中 | 禁止重复发送 |
| 401 | 清除失效 Token，进入登录流程 |
| 422 | 显示输入错误，不移除输入内容 |
| 429 | 显示限流提示，保留输入内容 |
| 502 | 保留用户消息，显示服务失败，不生成伪造回复 |
| 504 | 保留用户消息，允许重试，不生成伪造回复 |

## 联调检查表

- 新建 Companion 对话。
- 连续发送第二条消息。
- `conversation_id` 正确复用。
- Past Self 对话包含 `anchor_diary_id`。
- 422 不生成 AI 消息。
- 502/504 不生成伪造回复。
- 401 正确处理。
- 用户消息和 AI 消息都只出现一次。

## 并行开发流程

1. 共同冻结 Chat Contract。
2. 后端实现 Schema、Router、Service；前端实现 Type、API Client、Mock 页面逻辑。
3. 后端公布 OpenAPI 和真实 Fixture。
4. 前端替换 Mock，不改视觉层。
5. 运行契约测试和完整联调测试。
6. Contract、代码、测试一起合并。
