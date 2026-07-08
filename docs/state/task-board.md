# Inner Garden Task Board

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

## Backlog

| ID | Title | Priority | Estimate |
|----|-------|----------|----------|
| B-001 | Frontend Chat UI Components | High | 2-3 days |
| B-002 | Expand Chat Backend Regression Tests | Medium | 1 day |
| B-003 | Chat E2E Tests | Medium | 1 day |
| B-004 | Deployment Setup | Low | 1 day |
