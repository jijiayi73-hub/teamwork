# Log 34 - VPS Deployment Fix

Date: 2026-07-09
Branch: `codex/sync-scripts-to-main`
Task: TASK-027 VPS deployment closeout

## Request

Continue the VPS deployment from a pasted terminal transcript where Docker was restarted, image builds were slow, `docker compose up -d` was suspended with `^Z`, and `ssh vps` was mistakenly run from inside the VPS shell.

## Findings

- `/opt/inner-garden` existed on the VPS with `docker-compose.prod.yml`, `.env`, backend, and frontend files.
- No Inner Garden containers were running at the start of this pass.
- Docker was installed and active, but the DaoCloud registry mirror timed out while resolving `python:3.11-slim`.
- The backend Dockerfile on the VPS was older than the local Dockerfile and still used the default Debian package source.
- Installing `gcc` and `libpq-dev` in the backend image caused an `exit code 137` build failure after package download, consistent with the build process being killed under memory pressure.
- The backend then failed at runtime because `analysis_service.py` used `Session | None` while `Session` was only imported under `TYPE_CHECKING`.
- The frontend container served correctly on `127.0.0.1:8080`, but the healthcheck used `localhost`, which resolved to IPv6 `::1` inside the container and caused a false unhealthy state.

## Changes

| File | Change |
| --- | --- |
| `backend/Dockerfile` | Removed unnecessary `gcc` / `libpq-dev` install layer. |
| `backend/app/services/analysis_service.py` | Imported `sqlalchemy.orm.Session` at runtime. |
| `frontend/Dockerfile` | Changed healthcheck URL to `http://127.0.0.1:8080/`. |
| `docker-compose.yml` | Changed frontend healthcheck URL to `http://127.0.0.1:8080/health`. |
| VPS `/etc/docker/daemon.json` | Configured Tencent Cloud mirror first, DaoCloud second. |
| VPS `/opt/inner-garden/docker-compose.prod.yml` | Changed frontend healthcheck URL to `http://127.0.0.1:8080/health`. |

## Validation

```bash
py -c "from app.main import app; print('backend import ok')"
# backend import ok

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml build backend"
# Image inner-garden-backend Built

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml build frontend"
# Image inner-garden-frontend Built

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml ps"
# inner-garden-backend healthy
# inner-garden-frontend healthy

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"
# SQLite migration context completed without error

ssh vps "curl -fsS http://127.0.0.1:8000/health"
# {"success":true,"data":{"status":"healthy"},"message":"ok","request_id":"local"}

ssh vps "curl -I -sS http://jijiayi.online/ | head -n 8"
# HTTP/1.1 200 OK

ssh vps "curl -sS --max-time 10 http://jijiayi.online/api/v1/health"
# {"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}
```

## Remaining Risks

- `/opt/inner-garden/.env` still contains `DEEPSEEK_API_KEY=YOUR_KEY`; AI provider calls may fail until a real key is set.
- SSL is not configured yet; the verified public URL is HTTP.
- There are other Nginx site symlinks still enabled (`listen`, `listen.jijiayi.online.conf`), but `jijiayi.online` responded correctly in this verification.
