# Log 14 - Liquid Memory Background

## Date and Branch

- Date: 2026-07-08
- Branch: `frontend/home-demo`

## User Request

Integrate a liquid refraction inspired background into the Memory Garden experience, using the user-provided `memory.jpg` as the visual base. The effect should apply to both Memory Garden and Memory Detail while preserving existing UI layout, cards, buttons, navigation, routes, and data logic.

The user explicitly required a staged workflow:

1. Inspect the current project.
2. Inspect `feitangyuan/liquid-refraction-lab`.
3. Clarify requirements.
4. Provide an implementation plan.
5. Wait for confirmation before coding.

Implementation started only after the user confirmed.

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `frontend/README.md`
- `docs/vibe-logs/log-11-particle-wave-frontend-sync.md`
- `docs/vibe-logs/log-13-migration-hardening.md`

Note: `references/log-and-planning.md` was referenced by the workflow skill but is not present in this checkout.

## External Reference Reviewed

- `feitangyuan/liquid-refraction-lab` README
- `feitangyuan/liquid-refraction-lab` package metadata
- `components/ui/refraction-stage.tsx` from the reference repository

Key finding: the reference repository does not expose a clear license in the inspected files, so its source code was not copied. The implementation uses a clean-room Three.js shader approach inspired by the visual behavior: liquid flow, pointer disturbance, trailing feel, chromatic aberration, glow, and image refraction.

## Files Changed

### Modified Files

- `frontend/src/App.jsx`
  - Imports `LiquidMemoryBackground`.
  - Shows the liquid background only for `garden` and `detail` routes.
  - Keeps the old `DreamBackdrop` for all other routes.

- `frontend/src/styles.css`
  - Adds fixed background layer styles.
  - Adds static/reduced-motion fallback styles.
  - Slightly increases glass opacity and blur on Memory routes for readability.

### New Files

- `frontend/src/components/LiquidMemoryBackground.jsx`
  - Encapsulates all Three.js/WebGL background behavior.
  - Handles pointer movement, liquid distortion, chromatic aberration, glow, particles, resize, reduced motion, WebGL fallback, and cleanup.

- `frontend/public/memory-garden-bg.jpg`
  - Copied from `C:\Users\FZF\Desktop\memory.jpg`.
  - Used by the background component as `/memory-garden-bg.jpg`.

## Key Decisions and Constraints

- No dependency was added. The implementation uses existing `three@0.185.1`.
- The open-source reference code was not copied because the license was not clear.
- The background component is isolated from MemoryGarden page logic.
- The background layer uses `pointer-events: none`; pointer movement is observed through passive window listeners.
- Existing routes, API calls, card rendering, text, buttons, and navigation were left unchanged.
- The old gradient/particle `DreamBackdrop` remains in place for non-memory pages and as a practical rollback path.
- WebGL resources are disposed on unmount: animation frame, listeners, texture, geometry, material, renderer, and canvas.

## Verification

### Build

Command:

```bash
C:\Users\FZF\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe .\node_modules\vite\bin\vite.js build
```

Result:

- Build passed.
- Vite emitted a chunk-size warning because Three.js is included in the route bundle; this is a warning, not a build failure.

### Browser Preview

Checked in the in-app browser:

- `http://localhost:5173/#/memory-garden`
- `http://localhost:5173/#/memory-garden/1`

Results:

- Liquid background container exists.
- WebGL canvas exists.
- Vite error overlay is not present.
- Memory Garden content remains visible.
- Memory Detail route also receives the liquid background.

Known unrelated behavior:

- The page still shows `Request failed: 500` when backend diary/stat APIs fail. This was already present and is not caused by the visual background change.

## Rollback

Fast rollback options:

1. In `frontend/src/App.jsx`, replace the route-aware background expression with `<DreamBackdrop />`.
2. Remove `LiquidMemoryBackground.jsx` and the liquid CSS block if the feature is no longer needed.
3. Keep or delete `frontend/public/memory-garden-bg.jpg` depending on whether a static image fallback is still desired.

## Next Requirement Plan

- Product: decide whether the liquid effect should become the default Memory visual language or remain a page-specific experiment.
- Frontend: tune shader parameters after visual review, especially `pointerStrength`, `pointerRadius`, `chromaticAberration`, and particle count.
- Performance: consider lazy-loading the background component if bundle size becomes important.
- Accessibility: keep reduced-motion fallback enabled and verify the static fallback visually.
- Demo: capture before/after screenshots for Memory Garden and Memory Detail once the final visual strength is approved.
