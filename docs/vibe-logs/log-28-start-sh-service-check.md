# Log 28: start.sh Service Check

Date: 2026-07-09

Branch: `fix/auth-json-response`

## User Request

用户询问现有服务是否正常启动，并要求检查 `start.sh`。

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`

Note: workflow referenced `references/log-and-planning.md`, but this checkout does not contain that file.

## Findings

- Existing backend service was not healthy at first: port 8000 was not listening, and `logs/backend.log` showed the old `backend/venv` Python 3.9 runtime failing on `Response | None`.
- Frontend had started on 5173, but its API proxy logged `ECONNREFUSED` for `/api/v1/auth/register` because backend 8000 was unavailable.
- `scripts/start.sh` had a Bash-invalid `goto start_services` fast path. Because the failure was swallowed with `|| true`, the script could continue into the install path instead of doing a real quick start.
- `scripts/start.sh` used `backend/venv`, which was Python 3.9.6, while the documented backend requirement is Python 3.11+.
- `scripts/start.sh` and `scripts/stop.sh` lacked execute permission even though `README.md` documents `./scripts/start.sh` and `./scripts/stop.sh`.
- `backend/data/app.db` was empty, so auth register failed with `sqlite3.OperationalError: no such table: users`.
- The latest `message_sources` Alembic migration assumed an old `excerpt` column and failed on a fresh database where `0002` already created `excerpt_snapshot`.

## Changes

- `scripts/start.sh`: removed the invalid `goto` flow.
- `scripts/start.sh`: added Python 3.11+ detection.
- `scripts/start.sh`: standardized backend virtualenv usage on `backend/.venv`, which is Python 3.11.14 in this checkout.
- `scripts/start.sh`: runs `python -m alembic upgrade head` before starting backend.
- `scripts/start.sh`: starts backend without `--reload` for stable course-demo startup.
- `scripts/start.sh`: binds local services to `127.0.0.1` and added post-start health checks for `http://127.0.0.1:8000/api/v1/health` and `http://127.0.0.1:5173`.
- `scripts/start.sh` and `scripts/stop.sh`: restored executable permissions.
- `backend/alembic/versions/b76715ea8730_fix_message_sources_schema.py`: made the migration a no-op when `message_sources` already has `excerpt_snapshot`; it still converts old `excerpt` schemas when needed.

## Verification

```bash
bash -n scripts/start.sh
bash -n scripts/stop.sh
test -x scripts/start.sh && test -x scripts/stop.sh
```

Result: all passed.

Sandboxed service startup failed because local port binding was blocked:

```text
ERROR: [Errno 1] error while attempting to bind on address ('127.0.0.1', 8000): operation not permitted
```

Running `./scripts/start.sh` outside the sandbox passed the script health checks:

```text
后端 API 已就绪
前端界面 已就绪
```

Follow-up sandbox-external checks:

```bash
curl -i http://localhost:8000/api/v1/health
curl -I http://localhost:5173
```

Results:

- Backend returned `HTTP/1.1 200 OK` with JSON body `{"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}`.
- Frontend returned `HTTP/1.1 200 OK` with `Content-Type: text/html`.
- `POST /api/v1/auth/register` returned `HTTP/1.1 201 Created`, proving the `users` table exists and auth registration works.
- `PYTHONPYCACHEPREFIX=.codex_tmp/pycache backend/.venv/bin/python -m pytest backend/tests/test_auth.py -q` passed: 16 tests, 27 warnings.

## Current Service State

At the end of this check, both services were stopped and ports 8000/5173 were clear.

## Next Requirement Plan

- Product/demo: keep `README.md` launch commands aligned with executable scripts.
- Backend: keep Python 3.11+ as a hard startup requirement.
- Frontend: keep Vite at 5173 for local demo consistency.
- Tests: add a lightweight smoke script later if the team wants one-command CI validation for startup health.
