# Vibe Log 25: Frontend Auto Cover Generation

Date: 2026-07-09

## Summary

Implemented the frontend side of automatic Memory Card cover generation. The chat-to-card flow no longer exposes custom image upload controls to users. Instead, the app derives a poetic watercolor image prompt from the conversation and diary context, calls the existing AI image generation API, and saves the generated cover URL on the Memory Card.

## Changes

| Area | File | Change |
| --- | --- | --- |
| Chat UI | `frontend/src/AppFixed.jsx` | Removed user-facing image upload state, file input, upload button, preview backdrop, and upload-based draft cover data |
| Diary Result UI | `frontend/src/AppFixed.jsx` | Replaced manual cover URL/upload controls with a read-only automatic cover prompt preview |
| Save Flow | `frontend/src/AppFixed.jsx` | Calls AI image generation after `createDiary()` and before `createMemory()` |
| Prompt Generation | `frontend/src/AppFixed.jsx` | `buildWatercolorPrompt()` now uses title, emotion, diary content, raw transcript, and conversation messages |
| API Client | `frontend/src/api/client.js` | Added `generateImage()` helper for `POST /api/v1/images/generate` |
| Syntax Repair | `frontend/src/AppFixed.jsx` | Fixed mojibake-broken JSX and string literals that blocked build validation |

## Behavior

1. User chats with the companion.
2. User clicks "我说完了，生成日记".
3. Draft stores conversation messages and an auto-generated cover prompt.
4. On Diary Result, the user can review the prompt but cannot manually upload/select a cover image.
5. On save, frontend creates the diary, calls `/api/v1/images/generate`, then creates the Memory Card with the generated image URL and prompt.
6. If image generation fails, the Memory Card is still saved with the prompt so the diary is not lost.

## Validation

```bash
cd frontend
npm.cmd run build
# passed; Vite chunk-size warning only

npm.cmd run test:contract
# chat adapter contract ok
# auth invalidation ok
```

## Contract Notes

- No backend contract changed.
- Existing endpoint consumed by frontend: `POST /api/v1/images/generate`.
- Existing response field used: `data.image_url`.

## Risk

- Real image generation still depends on configured provider credentials and model support.
- When image generation fails, the current fallback is saving the Memory Card without `cover_image_url` but preserving `cover_prompt`.
