# Frontend Workflow

## Scope

Use this module for React, TypeScript, Vite, Three.js, UI state, page flow, components, and frontend API access.

## Rules

- All API requests go through the shared API Client.
- Shared request and response types live in a shared types location.
- Do not duplicate `fetch` logic across components.
- Do not use `any` to hide contract problems.
- Do not hard-code backend response data in the frontend.
- Pages must handle `loading`, `empty`, and `error`.
- AI failures must show failure state and offer retry when appropriate.
- Keep presentation and business request logic separated where practical.
- Make the feature work before visual polishing.
- Visual effects must not break core operations.

## Validation

Before assuming a script exists, inspect `package.json`. Prefer existing scripts in this order when relevant:

1. typecheck
2. lint
3. test
4. build

Record every command actually run.
