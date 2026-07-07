# Log 03: Core Feature

## 2026-07-07 后端基础闭环与前端需求澄清

### 本次实现记录

后端已完成第一阶段基础闭环函数：

- `POST /api/v1/conversations`：开始一次记录会话。
- `POST /api/v1/conversations/{conversation_id}/messages`：保存用户文字，并返回一条陪伴式回复。
- `GET /api/v1/conversations/{conversation_id}`：查询当前会话历史。
- `POST /api/v1/conversations/{conversation_id}/diary`：根据该会话下全部用户文字生成日记，并保存进 SQLite。
- `GET /api/v1/diaries`：查询已保存日记列表。
- `GET /api/v1/diaries/{diary_id}`：查询单篇日记详情。

当前实现采用 FastAPI + Pydantic + SQLite，应用启动时自动建表。陪伴式回复和日记生成暂时使用规则模板，尚未接入真实 AI Provider。

### 验证记录

已完成以下验证：

- 使用项目内 Python 缓存路径执行 `python3 -m compileall backend/app`，编译通过。
- 启动本地 Uvicorn 服务，使用临时 SQLite 数据库完成 HTTP 闭环验证。
- 验证流程包括：创建会话、发送文字、获得陪伴回复、生成日记、查询日记列表。

### 文档合规核验

当前代码与文档一致的部分：

- API 基础路径使用 `/api/v1`。
- 请求和响应字段使用 snake_case。
- 时间字段返回 ISO 8601 字符串。
- 后端使用 FastAPI 和 Pydantic。
- 数据落入 SQLite。
- 前端需要通过后端接口查询日记，而不是自行生成或保存日记。

当前代码与终版设计文档存在差距的部分：

- 初版基础实现曾直接使用标准库 `sqlite3`，不符合 SQLAlchemy/repositories 分层要求；该问题已在 `log-06-workflow-self-check.md` 对应任务中修复为 SQLAlchemy models + repositories。
- 终版设计要求 Auth、User、Entry、EmotionAnalysis、Diary、Report 等完整模型；当前仅实现 Conversation、ConversationMessage、Diary 三类基础表。
- 终版设计要求 AI Provider 抽象层和结构化情绪分析；当前仅有规则模板，未保存完整 `emotion_analyses`。
- 终版设计要求 JWT 和 bcrypt；当前基础闭环暂未实现登录鉴权。

结论：当前实现适合作为前端联调和课程演示的最小可运行闭环，但不能视为终版架构完成。后续需要补齐 Alembic migration、鉴权、Entry、EmotionAnalysis、统计接口和真实 AI Provider。

### 前端下一步需求

前端当前应优先补齐：

- 记录会话页：创建会话、发送文字、展示用户消息和陪伴回复。
- 生成日记操作：点击按钮调用后端生成接口，并展示生成结果。
- 日记历史页：调用后端列表接口展示已保存日记。
- 日记详情页：调用详情接口展示完整日记正文。
- API 请求封装：新增 conversations 和 diaries 请求文件，不在页面里散写 URL。

详细需求已写入：

- `docs/requirements/project-requirements.md`
- `docs/requirements/user-stories.md`
