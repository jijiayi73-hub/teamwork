# Inner Garden Known Issues

## 2026-07-09 最新更新

### I-013 新增：VPS 认证只读数据库错误

**问题描述**：VPS 生产环境无法注册和登录，后端报错 `attempt to write a readonly database`。

**根本原因**：
1. `docker-compose.prod.yml` 配置 `user: "1000:1001"`，但数据目录归 uid 999 所有
2. Dockerfile 创建的 `appuser` uid 为 999，与 docker-compose 配置不一致

**修复内容**：
| 操作 | 命令 |
|------|------|
| 修改数据目录权限 | `sudo chown -R 1000:1001 /opt/inner-garden/backend/data/` |
| 重启后端容器 | `docker compose -f docker-compose.prod.yml restart backend` |

**验证结果**：
- 注册功能：✅ 正常
- 登录功能：✅ 正常
- 详见：`docs/vibe-logs/log-37-vps-auth-readonly-database-fix.md`

---

## 2026-07-09 最新更新

### I-012 新增：Auth.js readJsonResponse 未定义错误

**问题描述**：生产环境报错 `readJsonResponse is not defined`，导致登录功能无法使用。

**根本原因**：
1. `frontend/src/api/auth.js` 中的 `login()` 和 `register()` 函数调用了 `readJsonResponse()` 函数，但该函数未定义
2. `login()` 函数中缺少 `fallback` 变量定义

**修复内容**：
| 文件 | 修复内容 |
|------|----------|
| `frontend/src/api/auth.js` | 添加 `readJsonResponse()` 辅助函数定义 |
| `frontend/src/api/auth.js` | 在 `login()` 函数中添加 `fallback` 变量 |

**验证结果**：
- `npm run build` 全部通过（✓ built in 2.00s）✅

---

## 2026-07-09 最新更新

### I-011 新增：AI Chat 对话框布局错位

**问题描述**：AI Companion Chat 界面的对话框 (`.composer-shell`) CSS 定义了 3 列，但 HTML 有 4 个元素，导致布局错位。

**修复内容**：
| 文件 | 修复内容 |
|------|----------|
| `frontend/src/styles.css` | 更新 `.composer-shell` 的 `grid-template-columns` 从 `minmax(0, 1fr) 42px 42px` 改为 `42px minmax(0, 1fr) 42px 42px` |

**验证结果**：
- `npm run build` 全部通过（✓ built in 1.80s）✅

---

## 2026-07-09 最新更新

### I-010 新增：Memory Card 删除时关联 Conversation 清理

**问题描述**：删除 Memory Card 时，只在前端隐藏，数据库中的 MemoryCard 被软删除，但关联的 Past Self Conversation 没有被删除。

**修复内容**：
| 文件 | 修复内容 |
|------|----------|
| `backend/app/routers/memories.py` | 更新 `delete_memory()` 函数，查找并软删除所有关联的 Conversation |
| `backend/tests/test_memories.py` | 新增 `test_delete_memory_card_deletes_associated_conversations` 测试 |

**验证结果**：
- `py -m pytest tests/test_memories.py` 全部通过（5 passed）✅
- `py -m pytest tests/e2e/test_memory_flow.py` 全部通过（12 passed）✅
- 详见：`docs/vibe-logs/log-21-memory-card-deletion-fix.md`

---

## 2026-07-08 最新风险补充

### I-001 更新：openai 依赖已加入 requirements

已修复：`backend/requirements.txt` 已加入 `openai`，并已通过 `py -m pip install -r requirements.txt` 安装。DeepSeek 使用 OpenAI-compatible SDK，真实直连 API 和 authenticated Chat 请求均已验证。

### I-002 更新：核心 Chat 测试已补齐并通过

旧记录中的“No Chat Test Coverage”已经过期。当前已有：

- `backend/tests/test_chat_api.py`
- `backend/tests/test_chat_service.py`
- `backend/tests/test_retrieval_service.py`
- `backend/tests/test_safety_service.py`
- `backend/tests/chat_test_utils.py`

本轮复跑结果：`21 passed, 3 warnings`。

### I-005 更新：真实服务启动和 authenticated Chat 请求已验证

用户已运行 `py -m uvicorn app.main:app --reload`，服务启动成功；用户侧 PowerShell 验证 `/health`、`/api/v1/health`、`/docs`、`/openapi.json` 可访问，OpenAPI 中可见 Chat 路由。

已完成：对真实运行服务发起 authenticated Chat 请求，并完成真实 DeepSeek Provider 调用。

### I-006 新增：pytest cache 写入警告

pytest 输出 `PytestCacheWarning`，提示 `.pytest_cache` 部分路径无法写入。该警告不影响本轮 21 项断言结果，但建议后续清理缓存权限或目录状态。

## Last Updated: 2026-07-08

## 2026-07-08 最新风险补充

### I-009 新增：Conversation History 500 错误已修复

**问题描述**：前端 `continueConversation(id)` 调用 `GET /api/v1/chat/conversations/{id}/messages` 返回 500 错误。

**根本原因**：数据库表 `message_sources` 缺少 `diary_date_snapshot`, `title_snapshot`, `excerpt_snapshot`, `emotion_label_snapshot` 列，且使用 `excerpt` 而非 `excerpt_snapshot`。这是因为表在 migration 0002 之前被手动创建，migration 被跳过。

**修复内容**：
| 文件 | 修复内容 |
|------|----------|
| `backend/alembic/versions/b76715ea8730_fix_message_sources_schema.py` | 新 migration 重建 `message_sources` 表，添加缺失的 snapshot 列 |

**验证结果**：
- `GET /api/v1/chat/conversations/{id}/messages` 返回 200 ✅
- `py -m pytest tests/test_chat_api.py` 全部通过（9 passed）✅
- 详见：`docs/vibe-logs/log-20-conversation-list-500-fix.md`

## 2026-07-08 最新风险补充

### I-001: Missing openai Dependency
- **Severity**: 🔴 High
- **Impact**: Chat feature cannot start
- **Component**: Backend
- **Workaround**: None
- **Fix**: Add `openai` to `backend/requirements.txt` and install

```bash
# Fix command
echo "openai" >> backend/requirements.txt
pip install -r backend/requirements.txt
```

## High Priority Issues

*No high priority issues at this time.*

## Medium Priority Issues

### I-002: Chat Test Coverage Still Expandable
- **Severity**: 🟡 Medium
- **Impact**: Current core Chat tests pass, but real startup, real provider, and E2E are not covered yet
- **Component**: Backend Tests
- **Workaround**: Use the current 21 passing tests for core regression, then add startup/E2E tests before release
- **Fix**: Expand the existing Chat test files instead of creating a single `test_chat.py`

### I-003: Missing Frontend Chat UI
- **Severity**: 🟡 Medium
- **Impact**: Cannot use chat feature from frontend
- **Component**: Frontend
- **Workaround**: Use API clients (curl, Postman)
- **Fix**: Create ChatWindow, MessageBubble components

## Low Priority Issues

### I-004: No State Tracking Infrastructure
- **Severity**: 🟢 Low
- **Impact**: Project progress not formally tracked
- **Component**: Documentation
- **Workaround**: Ad-hoc communication
- **Fix**: (Fixed with this document)

## Resolved Issues

| ID | Title | Resolved Date | Solution |
|----|-------|---------------|----------|
| I-000 | No Chat Database Schema | 2026-07-08 | Implemented conversations, messages, message_sources tables |
| I-000 | No Chat API Endpoints | 2026-07-08 | Implemented 6 REST endpoints |
| I-007 | Memory Garden 409 Save Error | 2026-07-08 | Frontend now checks for existing memory cards and handles 409 gracefully (log-19-409-save-fix.md) |
| I-009 | Conversation History 500 Error | 2026-07-08 | Migration b76715ea8730 fixed message_sources table schema (log-20-conversation-list-500-fix.md) |
