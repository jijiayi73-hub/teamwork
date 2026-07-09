# Log 17 - Diary Save Fallback

## Date and Branch

- Date: 2026-07-08
- Branch: frontend/home-demo

## User Request

Fix the existing diary save failure where clicking "保存到 Memory Garden" can show "保存失败：Request failed: 500". The fix must stay scoped to saving the generated diary into Memory Garden and avoid UI, layout, route, stack, or unrelated behavior changes.

## Source Docs

- README.md
- docs/design/system-architecture.md
- docs/design/technology-stack.md
- docs/design/api-design.md
- docs/design/database-design.md
- frontend/README.md
- backend/README.md

`references/log-and-planning.md` was requested by the workflow but is not present in this repository.

## Files Changed

- frontend/src/App.jsx

## Key Decisions

- Kept `/api/v1/diaries` as the primary real save API.
- Preserved the existing frontend pages, routes, styles, layout, buttons, and visual behavior.
- Added a local Memory Garden fallback only when the backend save/read path fails, so the user can still see the saved diary card in Memory Garden during local demo failures.
- Kept local fallback data shaped like a diary object so the existing Memory Garden list and detail page can render it without new UI components.

## Verification

- `cmd /c npm run build` passed.
- Browser verification on `http://localhost:5174/#/diary-result`:
  - Clicked "保存到 Memory Garden".
  - The app navigated to `#/memory-garden/local-...`.
  - Returning to `#/memory-garden` showed the newly saved local memory card in the existing card grid.
- Duplicate-card follow-up:
  - Confirmed the visible repeated cards were `local-...` fallback records, not extra SQLite `diaries` rows.
  - Updated local fallback ids and localStorage normalization so repeated saves of the same draft keep one Memory Garden card.
  - Repeated save verification kept one corresponding local card after refresh.

## Blockers and Risks

- `http://localhost:8000/api/v1/health` timed out, and the frontend proxy health check returned 500 during diagnosis. This means the real backend service was not reliably available in the local preview.
- The fallback is localStorage-based and intended to preserve the demo loop when the backend is unavailable. Once the backend is healthy, the app still prefers `/api/v1/diaries`.

## Next Requirement Plan

- Backend: make the local startup path reliable so `/api/v1/health`, `/api/v1/entries`, and `/api/v1/diaries` are available together.
- Frontend: keep the current save flow pointed at `/api/v1/diaries`; only remove the local fallback after the backend is stable enough for the demo.
- Proof before merge: create a diary, save it, refresh Memory Garden, and confirm the card appears from the real backend response.
