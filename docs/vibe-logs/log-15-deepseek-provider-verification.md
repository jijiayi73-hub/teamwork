# Log 15 - DeepSeek Provider 验证

## Log ID and Date

- Log ID: 15
- Date: 2026-07-08
- Branch: `backend/chat-database-schema`
- Related Task: TASK-001

## Goal

检索项目中新增的 DeepSeek API 配置与实现，跑一遍真实验证，确认 Chat 模块可以通过 DeepSeek Provider 完成 authenticated Chat 请求。

## Existing Context

项目 Chat 模块通过 `backend/app/services/ai_provider.py` 封装 AI Provider。DeepSeek 接入方式为 OpenAI-compatible API：

- `AI_PROVIDER=deepseek`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `AI_DEFAULT_MODEL=deepseek-chat`

## Progress Truth Audit Summary

| Claim | Evidence read | Verdict |
| --- | --- | --- |
| DeepSeek 配置已加入项目 | `backend/app/config.py`, `backend/.env` masked check | verified |
| DeepSeek 使用 OpenAI-compatible client | `backend/app/services/ai_provider.py` | verified |
| Python 环境具备 openai SDK | `py -m pip install -r requirements.txt` | verified |
| DeepSeek 直连 API 可用 | `py tests\test_deepseek_api.py` | verified |
| AIProvider 可用 DeepSeek 初始化 | `py tests\test_deepseek_api.py` | verified |
| authenticated Chat 请求可生成 assistant 消息 | PowerShell authenticated request against running server | verified |
| API key 未泄露到日志 | 输出中仅使用 `[masked]` | verified |

## Key Prompts

用户要求：

> 我添加了deepseek api /innergarden 检索项目跑一遍验证

## AI Proposed Plan

1. 搜索项目中的 DeepSeek、AI Provider、base URL、API key 配置。
2. 检查 `.env` 是否配置 DeepSeek，但不输出密钥。
3. 检查依赖是否包含 OpenAI-compatible SDK。
4. 安装缺失依赖。
5. 运行 DeepSeek 专项脚本。
6. 运行 Chat 自动化回归测试。
7. 对真实运行服务发起 authenticated Chat 请求。
8. 修复验证中发现的小契约问题，并再次回归。

## Human Checks and Validation

### 环境配置检查

`backend/.env` 中确认：

- `AI_PROVIDER=deepseek`
- `DEEPSEEK_API_KEY=[set]`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `AI_DEFAULT_MODEL=deepseek-chat`

### 依赖安装

```bash
cd backend
py -m pip install -r requirements.txt
```

结果：成功安装 `openai 2.44.0` 及其依赖。

### DeepSeek 专项脚本

```bash
py tests\test_deepseek_api.py
```

结果：

- Direct API Call: PASS
- AI Provider: PASS
- DeepSeek 返回模型：`deepseek-v4-flash`
- API key 输出已 mask

### Chat 回归测试

```bash
cd backend
py -m pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_retrieval_service.py tests/test_safety_service.py -v --tb=short
```

结果：`21 passed, 3 warnings`。

### Authenticated Chat 真实请求

验证动作：

1. `POST /api/v1/auth/register`
2. `GET /api/v1/auth/me`
3. `POST /api/v1/chat/messages`

结果：

- register_success: True
- auth_me_success: True
- chat_success: True
- user_role: user
- assistant_role: assistant
- message: message_sent
- 第二次复查 conversation `message_count=2`

## Problems Encountered

1. 初始验证发现 Python 环境缺少 `openai` 包，DeepSeek 适配器无法导入 OpenAI-compatible SDK。
2. `backend/requirements.txt` 未列出 `openai`，已补上。
3. 验证中发现 provider 错误响应详情仍硬编码为 `openai`，DeepSeek 错误时会误报来源；已改为 `settings.ai_provider`。
4. pytest 仍有 `.pytest_cache` 写入 warning 和 Starlette deprecation warning，不影响断言结果。

## Iterations

| Iteration | Action | Result |
| --- | --- | --- |
| 1 | 搜索 DeepSeek 配置和 Provider 实现 | 找到 `config.py`, `ai_provider.py`, `tests/test_deepseek_api.py` |
| 2 | 检查 `.env` 并 mask key | DeepSeek 配置存在 |
| 3 | 检查 openai SDK | 初始缺失 |
| 4 | 补 `requirements.txt` 并安装依赖 | 安装成功 |
| 5 | 跑 DeepSeek 专项脚本 | PASS |
| 6 | 跑 Chat 回归测试 | 21 passed |
| 7 | 跑 authenticated Chat 真请求 | PASS |
| 8 | 修正 provider 错误详情硬编码 | 回归仍 21 passed |

## Final Result

DeepSeek Provider 已完成真实验证；authenticated Chat 请求已通过，说明认证、Chat Router、ChatService、AIProvider、DeepSeek API 和消息持久化链路可以串通。

## Team Understanding and Reflection

DeepSeek 接入没有改变 Chat API 契约。它替换的是 AI Provider 底层供应商，接口层仍保持 `/api/v1/chat/messages` 的请求和响应结构。测试仍保留 Fake Provider 回归，真实 Provider 验证通过独立脚本和 authenticated request 完成。

## Related Files

| 文件 | 操作 | 原因 |
| --- | --- | --- |
| `backend/requirements.txt` | 更新 | 添加 `openai` SDK |
| `backend/app/services/chat_service.py` | 更新 | Provider 错误详情使用 `settings.ai_provider` |
| `backend/tests/test_chat_api.py` | 更新 | 断言 provider 错误详情存在合法 provider |
| `backend/tests/test_chat_service.py` | 更新 | 断言 provider 错误详情存在合法 provider |
| `docs/state/current-status.md` | 更新 | 记录 DeepSeek 验证结果 |
| `docs/state/task-board.md` | 更新 | 更新 TASK-001 进展 |
| `docs/state/known-issues.md` | 更新 | 标记 openai 依赖和 authenticated Chat 验证已完成 |
| `docs/contracts/chat-api.md` | 更新 | 更新尚未验证项 |
| `docs/vibe-logs/README.md` | 更新 | 增加 Log 15 索引 |

## Related Commit or PR

未提交。

## Conclusion

PASS: DeepSeek Provider、Chat 自动化回归和 authenticated Chat 真实请求均已验证通过。前端 UI/E2E 仍是后续工作。
