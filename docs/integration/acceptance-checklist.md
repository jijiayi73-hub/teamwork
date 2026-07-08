# Acceptance Checklist

## Chat Contract

- [ ] `docs/contracts/chat-api-v1.md` is reviewed by frontend and backend owners.
- [ ] Backend `/openapi.json` exposes all Chat paths.
- [ ] Any Pydantic schema change is checked against `/openapi.json`.
- [ ] Frontend types are generated from, or manually compared against, `/openapi.json`.
- [ ] Mock fixtures under `frontend/src/mocks/chat/` are copied from backend tests or real responses.

## Chat Integration

- [ ] New Companion conversation succeeds.
- [ ] Second message reuses `conversation_id`.
- [ ] Past Self conversation includes `anchor_diary_id`.
- [ ] 422 keeps input content and creates no AI message.
- [ ] 502 keeps saved user message and creates no fake assistant message.
- [ ] 504 keeps saved user message and allows retry.
- [ ] 401 clears invalid token and enters login flow.
- [ ] User message and assistant message each appear once.
