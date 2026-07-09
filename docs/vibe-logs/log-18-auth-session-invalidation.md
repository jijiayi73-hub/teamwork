# Vibe Log 18: Auth Session Invalidation

Date: 2026-07-08

Related Task: TASK-004

Related Commit or PR: Pending

## Goal

Locate and fix the issue shown in the runtime log where protected APIs repeatedly returned `401 Unauthorized` with `Inactive or missing user`.

## Existing Context

The backend authentication dependency decodes a bearer token, loads the user by `sub`, and rejects the request when the user is absent or not `active`. The frontend stores the access token and user object in localStorage and treated token presence as authenticated state.

## Progress Truth Audit Summary

| Claim | Evidence read | Verdict |
| --- | --- | --- |
| Chat and memory APIs require bearer auth | `docs/contracts/chat-api-v1.md`, `docs/contracts/memory-api-v1.md`, router dependencies | verified |
| The runtime failure is a 401 auth failure, not a schema or provider failure | User log excerpt with repeated `Inactive or missing user` on protected APIs | verified |
| Backend should continue returning 401 for missing or inactive users | `backend/app/auth/dependencies.py`, API contracts | verified |
| Frontend had no automatic stale-token invalidation on API 401 | `frontend/src/api/client.js`, `frontend/src/api/auth.js` before this task | verified |
| `.docx` progress reports can be used as evidence | `docs/reports/*.docx` file metadata and extraction attempt | unverified: files are 0 bytes |

## Key Prompts

User asked `/innergarden 根据日志定位并解决问题`.

## AI Proposed Plan

1. Confirm whether the log indicates backend startup, auth, API client, or database failure.
2. Preserve backend auth contract if the 401 is correct.
3. Add frontend stale-session invalidation on 401.
4. Add a focused regression test and run frontend checks.

## Human Checks And Validation

Commands actually run:

```bash
cd frontend
npm.cmd run test:contract
```

Result:

```text
chat adapter contract ok
auth invalidation ok
```

```bash
cd frontend
npm.cmd run build
```

Result:

```text
vite build passed after rerun outside sandbox
```

The first sandboxed build attempt failed with `Error: spawn EPERM` while starting esbuild. The same build passed after rerunning outside the sandbox.

## Problems Encountered

- The runtime logs repeated the same protected routes because the frontend still considered a stale local token to be an authenticated session.
- The backend warning about HMAC key length is real environment hardening feedback, but it was not the cause of these 401 responses.
- The `.docx` report files in `docs/reports/` are 0 bytes, so they could not support progress claims.

## Iterations

Initial hypothesis checked whether protected endpoints were receiving a token and whether backend auth was incorrectly rejecting it. Source review showed the backend behavior is contract-compliant. The fix moved to the frontend API boundary: clear stored auth and redirect to login when a protected API returns 401.

## Final Result

- `frontend/src/api/auth.js` exports `clearSession()` and `invalidateSession()`.
- `frontend/src/api/client.js` calls `invalidateSession()` for 401 responses.
- `frontend/src/api/authInvalidation.test.mjs` verifies stale-token cleanup, redirect preservation, and auth-change dispatch.
- `frontend/package.json` runs the new regression test as part of `npm.cmd run test:contract`.

## Team Understanding And Reflection

This is an integration-state problem rather than a backend route problem. When the development database is reset, seeded differently, or the logged-in user is deleted, old browser localStorage tokens must be treated as invalid. The backend should keep rejecting them, and the frontend should recover by returning the user to login.

## Related Files

- `frontend/src/api/auth.js`
- `frontend/src/api/client.js`
- `frontend/src/api/authInvalidation.test.mjs`
- `frontend/package.json`
- `docs/state/current-status.md`
- `docs/state/task-board.md`
