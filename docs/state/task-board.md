# Inner Garden Task Board

## 2026-07-09 Task Update: TASK-009 Memory Card Deletion Fix

### TASK-009: Memory Card Deletion with Associated Conversations
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-09 |
| **Completed** | 2026-07-09 |

#### 目标
更新删除逻辑，删除 Memory Card 时同时删除关联的 AI Companion Chat 聊天记录。

#### 实现内容
更新 `DELETE /api/v1/memories/{id}` 端点，在软删除 MemoryCard 的同时，查找并软删除所有关联的 Past Self Conversation（通过 `anchor_diary_id` 关联）。

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| Memories Router | 更新 `delete_memory()` 函数 | `backend/app/routers/memories.py` |
| Test Coverage | 新增测试验证关联删除 | `backend/tests/test_memories.py` |
| Documentation | 新建 Vibe Log | `docs/vibe-logs/log-21-memory-card-deletion-fix.md` |

#### 验证
```bash
py -m pytest tests/test_memories.py -v
# Result: 5 passed

py -m pytest tests/e2e/test_memory_flow.py -v
# Result: 12 passed
```

#### API 变更
- `DELETE /api/v1/memories/{id}` 响应新增 `deleted_conversations_count` 字段
- 返回删除的 Conversation 数量

#### 文档
- `docs/vibe-logs/log-21-memory-card-deletion-fix.md`

---

## 2026-07-09 Task Update: TASK-008 End-to-End Flow Testing

### TASK-008: End-to-End Flow Testing Implementation
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-09 |
| **Completed** | 2026-07-09 |

#### 目标
设计并实现端到端全流程测试，验证完整业务流程能否从头到尾跑通。

#### 实现内容
创建了完整的 E2E 测试套件，包含 64 个测试用例，覆盖以下 6 个核心流程：

1. **F-001: Authentication Full Flow** - 注册 → 登录 → 访问受保护资源 → 登出 → Token 失效验证
2. **F-002: Diary Creation Full Flow** - 创建日记条目 → 情绪分析 → 保存日记 → 查看列表 → 统计更新 → 删除
3. **F-003: Chat Full Flow** - 创建新对话 → 发送消息 → AI 回复 → 继续对话 → 查看历史 → 删除
4. **F-004: Memory Garden & Past Self Chat Flow** - 创建日记 → 上传封面 → 创建记忆卡片 → Past Self 聊天 → 删除
5. **F-005: Error Recovery Flows** - 无效 Token 恢复、AI 错误恢复、验证错误恢复、资源不存在恢复
6. **F-006: Multi-User Isolation Flow** - 用户数据隔离验证

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| E2E Test Plan | 新建 | `docs/integration/e2e-test-plan.md` |
| E2E Test Suite | 新建 | `backend/tests/e2e/` 目录及所有测试文件 |
| Test Configuration | 新建 | `backend/tests/e2e/conftest.py` (共享 fixtures) |
| Auth Flow Tests | 新建 | `backend/tests/e2e/test_auth_flow.py` |
| Diary Flow Tests | 新建 | `backend/tests/e2e/test_diary_flow.py` |
| Chat Flow Tests | 新建 | `backend/tests/e2e/test_chat_flow.py` |
| Memory Flow Tests | 新建 | `backend/tests/e2e/test_memory_flow.py` |
| Error Recovery Tests | 新建 | `backend/tests/e2e/test_error_recovery.py` |
| User Isolation Tests | 新建 | `backend/tests/e2e/test_user_isolation.py` |

#### 验证
```bash
cd backend
py -m pytest tests/e2e/ -v
# Result: 64 passed, 157 warnings in 15.37s
```

所有 E2E 测试通过：
- ✅ 8 个认证流程测试
- ✅ 9 个日记流程测试
- ✅ 13 个聊天流程测试
- ✅ 15 个记忆花园流程测试
- ✅ 11 个错误恢复测试
- ✅ 8 个用户隔离测试

#### 测试覆盖的关键场景
1. 完整用户旅程验证
2. 数据库状态验证
3. API 契约验证
4. 错误场景和恢复路径
5. 多用户数据隔离
6. 软删除和持久化验证

#### 文档
- `docs/integration/e2e-test-plan.md` - 测试计划和设计文档

---

## 2026-07-08 Task Update: TASK-007 Conversation History 500 Error Fix

### TASK-007: Conversation History 500 错误修复
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-08 |
| **Completed** | 2026-07-08 |

#### 问题
前端 `continueConversation(id)` 调用 `GET /api/v1/chat/conversations/{id}/messages` 返回 500 服务器错误，导致用户无法查看历史会话消息。

#### 根本原因
数据库表 `message_sources` 使用了过时的 schema，缺少以下列：
- `diary_date_snapshot`
- `title_snapshot`
- `excerpt_snapshot`（表中有 `excerpt` 而非 `excerpt_snapshot`）
- `emotion_label_snapshot`

这是因为表在 migration 0002 之前被手动创建，migration 被跳过（CREATE TABLE IF NOT EXISTS），但 alembic 仍记录为 version 0003。

#### 解决方案
创建 migration `b76715ea8730_fix_message_sources_schema.py`：
1. 创建正确结构的新表 `message_sources_new`
2. 迁移现有数据（`excerpt` → `excerpt_snapshot`）
3. 删除旧表并重命名新表
4. 重建索引

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| Database Migration | 新建 | `backend/alembic/versions/b76715ea8730_fix_message_sources_schema.py` |

#### 验证
- ✅ `GET /api/v1/chat/conversations/{id}/messages` 返回 200
- ✅ `GET /api/v1/chat/conversations` 返回 200
- ✅ `py -m pytest tests/test_chat_api.py` -> 9 passed
- ✅ 创建新会话并获取消息正常工作

#### 文档
- `docs/vibe-logs/log-20-conversation-list-500-fix.md`

---

## 2026-07-08 Task Update: TASK-006 Past Self Chat 500 Error Fix

### TASK-006: Past Self Chat 500 错误修复
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-08 |
| **Completed** | 2026-07-08 |

#### 问题
用户在 Memory Garden 页面 (/#/memory-garden/1) 使用 Past Self Chat 功能时返回 500 服务器错误。

#### 根本原因
后端多处代码直接访问 `diary.analysis.primary_emotion` 而未检查 `diary.analysis` 是否为 None。当 Diary 的 analysis 关系未加载、analysis 记录被删除或数据不一致时，会抛出 `AttributeError`。

#### 解决方案
在所有访问 `diary.analysis.primary_emotion` 的地方添加空值检查：
- `chat_service.py`: 3 处添加检查，使用 "未知" 作为默认情绪
- `retrieval_service.py`: 1 处添加检查，返回中性评分
- `stats.py`: 3 处添加检查，过滤或使用默认值

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| Chat Service | 添加空值检查 | `backend/app/services/chat_service.py` |
| Retrieval Service | 添加空值检查 | `backend/app/services/retrieval_service.py` |
| Stats Router | 添加空值检查 | `backend/app/routers/stats.py` |

#### 验证
- ✅ `py -m pytest tests/test_chat_api.py tests/test_memories.py` -> 13 passed
- ✅ `py -m pytest tests/ -k "stats or emotion"` -> 33 passed
- ✅ `py -m pytest tests/test_retrieval_service.py` -> 4 passed
- ✅ 后端服务健康检查正常

---

## 2026-07-08 Task Update: TASK-005 Memory Garden 409 Save Error Fix

### TASK-005: Memory Garden 409 Save Error
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-08 |
| **Completed** | 2026-07-08 |

#### 问题
用户在 Memory Garden 界面点击"保存到 Memory Garden"时返回 409 错误。

#### 根本原因
- 后端限制每个 entry 只能创建一个 diary，每个 diary 只能创建一个 memory card
- 用户重复保存相同草稿时，`createDiary` 返回 409 Conflict
- 前端未优雅处理此场景

#### 解决方案
在 `frontend/src/AppFixed.jsx` 的 `DiaryResultPage` 组件中：
1. 页面加载时检查该 entry_id 是否已存在 memory card
2. 如果已存在，显示"查看已保存的记忆卡片"按钮
3. 保存时捕获 409 错误，查找现有 memory card 并跳转

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| DiaryResultPage | 新增状态和逻辑 | `frontend/src/AppFixed.jsx` |

#### 验证
- ✅ `npm run build` 成功 (2.97s)
- ⏳ 用户端到端测试待验证

#### 文档
- `docs/vibe-logs/log-19-409-save-fix.md`

---

## 2026-07-08 Task Update: TASK-004 Auth Session 401 Loop Fix

### TASK-004: Stale Frontend Token Invalidation

| Field | Value |
| --- | --- |
| Owner | Codex |
| Branch | `codex/sync-scripts-to-main` |
| Status | Complete |
| Started | 2026-07-08 |
| Completed | 2026-07-08 |

| Component | Status | Files |
| --- | --- | --- |
| Frontend auth state | Complete | `frontend/src/api/auth.js` |
| API client 401 handling | Complete | `frontend/src/api/client.js` |
| Regression coverage | Complete | `frontend/src/api/authInvalidation.test.mjs`, `frontend/package.json` |
| Debug trace | Complete | `docs/vibe-logs/log-18-auth-session-invalidation.md` |

Validation:

- `npm.cmd run test:contract` -> chat adapter contract ok; auth invalidation ok.
- `npm.cmd run build` -> successful build after rerun outside sandbox; initial sandbox run failed with `spawn EPERM`.

Notes:

- No backend API status code, route, schema, or database behavior changed.
- The user-facing recovery path for stale tokens is now automatic logout plus redirect to `#/login`.

## 2026-07-08 Task Update: TASK-003 MVP Memory Loop Completion

### TASK-003: Memory Card / Past Self / Diary Result / Admin Dashboard Repair

| Field | Value |
| --- | --- |
| Owner | Codex |
| Branch | `codex/sync-scripts-to-main` |
| Status | Complete |
| Started | 2026-07-08 |
| Completed | 2026-07-08 |

| Component | Status | Files |
| --- | --- | --- |
| Memory Card DB/API | Complete | `backend/app/models/diary.py`, `backend/app/schemas/memories.py`, `backend/app/routers/memories.py`, `backend/alembic/versions/0003_add_memory_cards_and_uploads.py` |
| Past Self Chat | Complete | `backend/app/routers/memories.py`, `backend/tests/test_memories.py` |
| Image persistence | Complete | `POST /api/v1/uploads/images`, static `/uploads/...` mount |
| Admin chart stats | Complete | `backend/app/routers/admin.py`, `frontend/src/AppFixed.jsx` |
| Frontend MVP loop | Complete | `frontend/src/AppFixed.jsx`, `frontend/src/api/client.js`, `frontend/src/main.jsx`, `frontend/src/styles.css` |
| Auth error detail | Complete | `frontend/src/api/auth.js` |
| Contract/docs | Complete | `docs/contracts/memory-api-v1.md`, `docs/vibe-logs/log-17-memory-loop-completion.md` |

Validation:

- `py -m pytest tests/test_memories.py tests/test_admin.py tests/test_chat_api.py -q` -> 21 passed, 54 warnings.
- `npm.cmd run build` -> successful build; chunk-size warning only.

Notes:

- `frontend/src/AppFixed.jsx` is the active app entry via `frontend/src/main.jsx`; old `App.jsx` remains in place because the patch tool could not delete it during this run.
- Cover image generation is prompt-generation plus upload/URL selection, not a real image-model integration.

## 2026-07-08 最新任务更新：TASK-002 移除 Demo 自动登录，实现认证业务层

### TASK-002: 认证业务层与登录界面
| 字段 | 值 |
|---|---|
| **Owner** | jiayiji |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-08 |
| **Completed** | 2026-07-08 |

#### 变更内容

| 组件 | 操作 | 文件 |
|------|------|------|
| 认证业务层 | 新建 | `frontend/src/api/auth.js` |
| 登录页面组件 | 新建 | `frontend/src/components/LoginPage.jsx` |
| API 客户端 | 更新 | 移除 `ensureDemoSession()` 和 `DEMO_USER` |
| App.jsx | 更新 | 集成认证流程，添加登录路由，受保护路由检查 |
| TopNav | 更新 | 显示用户信息和登出按钮 |

#### 新增功能

- **认证业务函数** (`frontend/src/api/auth.js`):
  - `login(email, password)` - 用户登录
  - `register(username, email, password)` - 用户注册
  - `logout()` - 用户登出
  - `getCurrentUser()` - 获取当前用户
  - `isAuthenticated()` - 检查认证状态
  - `requireAuth()` - 路由守卫，未认证跳转登录页
  - `saveRedirectPath()` / `consumeRedirectPath()` - 登录后跳转

- **登录页面** (`frontend/src/components/LoginPage.jsx`):
  - 最小可用的登录/注册界面
  - 表单验证和错误提示
  - 登录/注册切换
  - 设计为后期可替换

- **路由保护**:
  - `/login` - 登录页面（公开）
  - `/ai-companion-chat` - 需要登录
  - `/memory-garden` - 需要登录
  - `/diary-result` - 需要登录
  - `/memory-garden/:id` - 需要登录

#### 后续扩展建议

1. **表单增强**:
   - 密码强度提示
   - 邮箱格式验证
   - 记住我功能

2. **UI 美化**:
   - 更精美的登录页设计
   - 添加品牌元素
   - 动画效果

3. **功能扩展**:
   - 忘记密码
   - 社交登录
   - 邮箱验证

---

## 2026-07-08 最新任务更新：TASK-001 Chat 测试收口

| 字段 | 值 |
| --- | --- |
| 当前状态 | Backend implemented; current Chat automated tests passing; runtime startup still pending |
| 本轮验证 | `py -m pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_retrieval_service.py tests/test_safety_service.py -v --tb=short` |
| 结果 | 21 passed, 3 warnings |
| 启动验证 | 用户运行 `py -m uvicorn app.main:app --reload` 成功；用户侧验证 `/health`、`/api/v1/health`、`/docs` 可访问 |
| OpenAPI 验证 | 用户侧 `/openapi.json` 输出 `/api/v1/chat/messages` 和 `/api/v1/chat/conversations*` |
| DeepSeek Provider 验证 | `py tests\test_deepseek_api.py` 通过；真实 authenticated Chat 请求返回 `message_sent` |
| 新增/确认测试文件 | `backend/tests/test_chat_api.py`, `backend/tests/test_chat_service.py`, `backend/tests/test_retrieval_service.py`, `backend/tests/test_safety_service.py`, `backend/tests/chat_test_utils.py` |
| 新增 API 文档 | `docs/contracts/chat-api.md` |

当前 TASK-001 不再应标记为“Backend Tests Pending”。更准确的状态是：核心 Chat 自动化测试已存在并通过当前测试集，真实 uvicorn 启动、OpenAPI 暴露、DeepSeek Provider 直连和 authenticated Chat 请求均已验证；前端 UI 和 E2E 仍待完成。

## Last Updated: 2026-07-08

## Active Tasks

### TASK-001: RAG Chat Implementation
| Field | Value |
|-------|-------|
| **Owner** | jiayiji |
| **Branch** | `backend/chat-database-schema` |
| **Status** | 🟡 Backend Complete, Pending Dependency & UI |
| **Started** | 2026-07-08 |
| **Completed** | - |

#### Deliverables

| Component | Status | Files |
|-----------|--------|-------|
| Database Schema | ✅ Complete | [models/chat.py](../backend/app/models/chat.py) |
| Pydantic Schemas | ✅ Complete | [schemas/chat.py](../backend/app/schemas/chat.py) |
| Retrieval Service | ✅ Complete | [services/retrieval_service.py](../backend/app/services/retrieval_service.py) |
| AI Provider Service | ✅ Complete | [services/ai_provider.py](../backend/app/services/ai_provider.py) |
| Safety Service | ✅ Complete | [services/safety_service.py](../backend/app/services/safety_service.py) |
| Chat Service | ✅ Complete | [services/chat_service.py](../backend/app/services/chat_service.py) |
| Chat Router | ✅ Complete | [routers/chat.py](../backend/app/routers/chat.py) |
| Main Integration | ✅ Complete | [main.py](../backend/app/main.py) |
| Frontend API Client | ✅ Complete | [frontend/src/api/chat.js](../frontend/src/api/chat.js) |
| Add openai to requirements.txt | ✅ Complete | `backend/requirements.txt` |
| Backend Tests | ✅ Current core set passing | `backend/tests/test_chat_api.py`, `backend/tests/test_chat_service.py`, `backend/tests/test_retrieval_service.py`, `backend/tests/test_safety_service.py` |
| Frontend UI Components | ❌ Pending | - |

#### Remaining Work

1. **Required Before First Run:**
   - DeepSeek provider dependency and environment have been verified.

2. **Optional (Completion):**
   - Expand Chat backend tests beyond the current 21 core cases if needed
   - Create frontend Chat UI components
   - Add E2E tests

3. **Verification:**
   - Run `uvicorn app.main:app --reload`
   - Test `POST /api/v1/chat/messages` endpoint
   - Verify both companion and past_self modes

---

## Completed Tasks

### TASK-000: Chat Database Schema
| Field | Value |
|-------|-------|
| **Owner** | - |
| **Branch** | `backend/chat-database-schema` |
| **Status** | ✅ Complete |
| **Completed** | 2026-07-08 |

See [log-12-chat-database-schema.md](../vibe-logs/log-12-chat-database-schema.md) for details.

---

## 2026-07-09 Task Update: TASK-011 Feature Migration Implementation

### TASK-011: Image Generation and Calendar Feature Migration
| Field | Value |
| --- | --- |
| **Owner** | Codex |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete |
| **Started** | 2026-07-09 |
| **Completed** | 2026-07-09 |

#### 目标
从 E:\teamwork-main 项目迁移图片生成和日历功能到当前项目。

#### 实现内容
1. **图片生成功能** - 新增 `generateFallbackCover`, `buildWatercolorPrompt`, `getCoverPalette`, `buildCardQuote` 等函数
2. **日历页面组件** - 新增完整的 `MonthlyReport` 组件，支持月份导航、情绪显示、详情弹窗
3. **路由集成** - 添加 `#/monthly-report` 路由和导航链接
4. **样式迁移** - 完整迁移月报相关 CSS 样式

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| 图片生成函数 | 新增 | `frontend/src/AppFixed.jsx` |
| 月报组件 | 新增 | `frontend/src/AppFixed.jsx` |
| 路由更新 | 更新 | `frontend/src/AppFixed.jsx` |
| 导航链接 | 更新 | `frontend/src/AppFixed.jsx` |
| 月报样式 | 新增 | `frontend/src/styles.css` |

#### 验证
```bash
cd frontend
npm run build
# Result: ✓ built in 2.94s
```

#### 文档
- `docs/vibe-logs/log-23-feature-migration-implementation.md` (待创建)

---

## 2026-07-09 Task Update: TASK-010 Feature Migration Analysis

### TASK-010: Voice, Image Generation, and Calendar Migration Analysis
| Field | Value |
| --- | --- |
| **Owner** | Analysis Team |
| **Branch** | `codex/sync-scripts-to-main` |
| **Status** | ✅ Complete (Analysis) |
| **Started** | 2026-07-09 |
| **Completed** | 2026-07-09 |

#### 目标
分析 E:\teamwork-main 项目中的语音输入、图片生成、日历功能实现，与当前项目结构比对，制定迁移计划。

#### 分析结果
| 功能 | E:\teamwork-main | 当前项目 | 迁移需求 |
|------|------------------|----------|----------|
| 语音输入 | ✅ 已实现 (App.jsx:156-177) | ✅ 已存在 (AppFixed.jsx:221-247) | ❌ 无需迁移 |
| 图片生成 | ✅ 本地SVG水彩 (App.jsx:696-739) | ❌ 不存在 | ✅ 需要迁移 |
| 日历功能 | ✅ 完整页面 (MonthlyReport.jsx) | ❌ 不存在 | ✅ 需要迁移 |

#### 迁移计划
| 阶段 | 内容 | 优先级 | 预计工时 |
|------|------|--------|----------|
| Phase 1 | 图片生成功能迁移 | HIGH | 2-3 小时 |
| Phase 2 | 日历页面组件迁移 | HIGH | 4-5 小时 |
| Phase 3 | 数据流集成 | MEDIUM | 2-3 小时 |
| Phase 4 | 样式迁移 | MEDIUM | 1-2 小时 |

#### 变更内容
| 组件 | 操作 | 文件 |
|------|------|------|
| 分析文档 | 新建 | `docs/vibe-logs/log-22-feature-migration-analysis.md` |
| 任务板 | 更新 | `docs/state/task-board.md` |

#### 文档
- `docs/vibe-logs/log-22-feature-migration-analysis.md` - 完整分析和迁移计划

---

## Backlog

| ID | Title | Priority | Estimate |
|----|-------|----------|----------|
| B-001 | Frontend Chat UI Components | High | 2-3 days |
| B-002 | Expand Chat Backend Regression Tests | Medium | 1 day |
| B-003 | Chat E2E Tests | Medium | 1 day |
| B-004 | Deployment Setup | Low | 1 day |
| B-005 | Image Generation Migration | High | 2-3 hours |
| B-006 | Monthly Report Calendar Migration | High | 4-5 hours |
| B-007 | Calendar Data Integration | Medium | 2-3 hours |
