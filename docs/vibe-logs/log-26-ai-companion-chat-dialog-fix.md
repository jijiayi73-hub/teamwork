# Log 26: AI Companion Chat Dialog Fix

Date: 2026-07-09

## Summary

Fixed the `/#/ai-companion-chat` composer dialog layout. The composer CSS expected four grid columns, but the page renders three controls: the textarea, voice button, and send button. That mismatch placed the textarea into a 42px icon-sized column.

## Changes

- `frontend/src/styles.css`: changed `.composer-shell` to a three-column grid: flexible textarea, voice button, send button.
- `frontend/src/AppFixed.jsx`: protected routes now return `LoginPage` immediately when `requireAuth()` redirects, avoiding a brief unauthorized chat render and 401 note.

## Verification

- `cd frontend && npm.cmd run build` passed after the known Windows sandbox `spawn EPERM` fallback.
- `cd frontend && npm.cmd run test:contract` passed: chat adapter contract ok; auth invalidation ok.
- Browser inspection on `http://localhost:5174/#/ai-companion-chat` reproduced the pre-fix textarea width of 42px and confirmed the root cause.
- Browser inspection after the route guard confirmed unauthenticated `/#/ai-companion-chat` renders the login page without mounting `.chat-window`.

## API / DB Impact

No backend API or database changes.
