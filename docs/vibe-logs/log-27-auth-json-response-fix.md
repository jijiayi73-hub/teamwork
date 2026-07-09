# Log 27: Auth JSON Response Fix

Date: 2026-07-09

Branch: `fix/auth-json-response`

## User Request

用户反馈登录/注册界面返回 `Unexpected end of JSON input`，导致无法正常运行。

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `backend/README.md`
- `frontend/README.md`

Note: workflow referenced `references/log-and-planning.md`, but this checkout does not contain that file.

## Root Cause

Two issues were found:

1. `backend/app/services/analysis_service.py` referenced `Session` in a runtime type annotation while importing it only under `TYPE_CHECKING`, which could stop the FastAPI app from importing under the project Python runtime.
2. `frontend/src/api/auth.js` called `response.json()` directly in `login()` and `register()`. When the backend/proxy returned an empty body or non-JSON error response, the browser raised the low-level JSON parse error instead of a user-readable auth error.

## Changes

- `frontend/src/api/auth.js`: added safe response parsing through `response.text()` plus guarded `JSON.parse()`.
- `frontend/src/api/auth.js`: changed login/register fallback errors to clear Chinese messages that point to backend startup or retry.
- `frontend/src/api/auth.js`: validated successful auth payloads before saving token/user data.
- `frontend/src/api/authEmptyResponse.test.mjs`: added regression coverage for empty error responses and non-JSON success responses.
- `frontend/package.json`: included the new regression test in `npm run test:contract`.
- `backend/app/services/analysis_service.py`: imported SQLAlchemy `Session` at runtime so app import and backend auth tests can run.

## Verification

```bash
cd frontend
npm run test:contract
```

Result:

```text
chat adapter contract ok
auth invalidation ok
auth empty response handling ok
```

```bash
cd frontend
npm run build
```

Result: Vite production build passed. Vite still reports the existing large chunk warning.

```bash
PYTHONPYCACHEPREFIX=.codex_tmp/pycache backend/.venv/bin/python -m pytest backend/tests/test_auth.py -q
```

Result: 16 passed, 27 warnings. A prior attempt with system `python3` failed because it is Python 3.9.6 while the backend requires Python 3.11+.

## API / DB Impact

No backend API, database schema, migration, or seed data changes.

## Risks

The fix prevents the UI from surfacing raw JSON parse failures. If the backend service is stopped, login/register still cannot succeed, but the page now shows a readable failure message.

## Next Requirement Plan

- Product: document a short acceptance criterion for auth error UX if login/register polish continues.
- Frontend: move remaining direct `fetch` auth code toward the documented shared API client pattern when the TypeScript API layer is consolidated.
- Backend: keep `/api/v1/auth/login` and `/api/v1/auth/register` returning `ApiResponse[TokenRead]` JSON.
- Tests: add browser-level smoke coverage once a Playwright or Vitest browser setup exists.
