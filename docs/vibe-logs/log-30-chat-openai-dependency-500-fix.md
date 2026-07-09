# Log 30: Chat openai Dependency 500 Fix

Date: 2026-07-09

Branch: `fix/auth-json-response`

## User Request

用户反馈发送聊天消息失败：

```text
发送失败：Request failed: 500。用户消息已保留，可以重试或生成草稿。
```

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `backend/README.md`
- `frontend/README.md`

Note: workflow referenced `references/log-and-planning.md` and `references/project-map.md`, but this checkout does not contain those files.

## Diagnosis

Backend log showed `POST /api/v1/chat/messages` failing while initializing the AI provider:

```text
ModuleNotFoundError: No module named 'openai'
app.services.ai_provider.AIConfigError: openai package not installed
```

The root cause was a stale backend virtual environment: `backend/requirements.txt` already listed `openai`, but `backend/.venv` did not have it installed. Because `scripts/start.sh` trusted the old `.installed` flag, it could skip dependency installation after requirements changed.

## Changes

- `backend/app/services/chat_service.py`: catch `AIConfigError` from provider initialization and return the existing readable `ai_service_unavailable` 502 response instead of leaking a raw 500.
- `backend/tests/test_chat_service.py`: added coverage for AI provider configuration errors preserving the user message and returning 502.
- `backend/tests/test_chat_api.py`: added API-level coverage for the same readable 502 behavior.
- `scripts/start.sh`: added requirements hash tracking inside `backend/.venv/.requirements.sha256`, so backend dependencies reinstall when `backend/requirements.txt` changes.
- Installed `openai==2.44.0` into the current `backend/.venv`.

## Architecture Notes

- No API route, request schema, database model, migration, or frontend request contract changed.
- Chat still goes through the documented AI provider adapter.
- User messages remain saved when AI provider initialization or generation fails.

## Verification

```bash
PYTHONPYCACHEPREFIX=.codex_tmp/pycache backend/.venv/bin/python -m pytest backend/tests/test_chat_service.py backend/tests/test_chat_api.py -q
bash -n scripts/start.sh
backend/.venv/bin/python -c "import openai; print(openai.__version__)"
```

Results:

- Chat tests passed: 14 passed.
- `scripts/start.sh` syntax check passed.
- Current backend venv can import `openai` version `2.44.0`.

The sandbox could not verify a live chat request because ports `8000` and `5173` were not running at the time of the final check.

## Next Requirement Plan

- Product/demo: after restarting services, retry the same chat message once from the UI.
- Backend: keep provider dependency/config errors user-readable and distinct from validation or auth failures.
- Frontend: continue preserving failed user messages so retry/draft remains possible.
- Tests: add a future smoke check that fails startup when required runtime packages are missing.
