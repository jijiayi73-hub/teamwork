# Log 29: start.sh LAN Access

Date: 2026-07-09

Branch: `fix/auth-json-response`

## User Request

用户要求 `start.sh` 允许服务通过局域网连接。

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `frontend/README.md`
- `backend/README.md`

Note: workflow referenced `references/log-and-planning.md` and `references/project-map.md`, but this checkout does not contain those files.

## Changes

- `scripts/start.sh`: changed default backend and frontend bind hosts from `127.0.0.1` to `0.0.0.0` so other devices on the same LAN can connect.
- `scripts/start.sh`: added `BACKEND_HOST`, `FRONTEND_HOST`, `BACKEND_PORT`, and `FRONTEND_PORT` environment-variable overrides.
- `scripts/start.sh`: kept health checks on `127.0.0.1` so startup validation remains local and stable.
- `scripts/start.sh`: added LAN IP detection and prints `http://<LAN_IP>:5173` plus backend/API docs LAN URLs after startup.
- `README.md`: documented the LAN access URL pattern for Linux / macOS startup.

## Architecture Notes

- No backend API route, schema, database table, migration, or frontend API client contract changed.
- Vite proxy remains pointed at `http://localhost:8000`; browser requests to `/api` still flow through the frontend dev server when users open the LAN frontend URL.
- If the OS firewall blocks inbound ports, the script can start successfully while other devices still cannot connect until ports `5173` and `8000` are allowed.

## Verification

```bash
bash -n scripts/start.sh
```

Result: passed.

Full service startup was not run in the sandbox because binding local ports is restricted in this environment.

## Next Requirement Plan

- Product/demo: use the script-printed LAN URL in classroom or team-device demos.
- Frontend: keep API calls relative to `/api/v1` so LAN users stay on the same origin through the Vite proxy.
- Backend: keep direct API docs available at the LAN backend URL for debugging.
- Tests: when outside the sandbox, run `./scripts/start.sh`, then test one phone or second laptop against the printed frontend URL.
