# Integration Matrix

| Area | Source of truth | Producer | Consumer | Required check |
| --- | --- | --- | --- | --- |
| Chat API fields | `backend/app/schemas/chat.py`, `/openapi.json`, `docs/contracts/chat-api-v1.md` | Backend | Frontend | Compare frontend adapter/types against `/openapi.json` before integration |
| Chat mock fixtures | Backend test fixture or real response | Backend | Frontend | Mock JSON shape matches success/error envelopes |
| Chat page state | `docs/integration/chat-frontend-mapping.md` | Frontend + Backend | Frontend | UI handles success, 401, 422, 502, 504 without duplicate messages |
| Contract tests | Backend pytest and frontend adapter tests | Backend + Frontend | CI/manual verification | Fail on renamed fields such as `role` to `sender` |

Do not use ad hoc field guesses during frontend/backend parallel development.
