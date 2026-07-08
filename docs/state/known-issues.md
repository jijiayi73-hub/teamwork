# Inner Garden Known Issues

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

## Critical Issues

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
