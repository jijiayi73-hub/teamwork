# Log 07 - Home Demo

## Date and Branch

- Date: 2026-07-07
- Branch: `frontend/home-demo`

## User Request

Build the first page only for a pure frontend "Mindful Memory Diary" demo. The user explicitly asked to confirm each page before coding, avoid backend/API/database/login work, use local mock data and `localStorage`, and implement only Home after confirmation.

Confirmed Home details:

- Main title: `Mindful Memory Diary`
- Chinese subtitle: `把今天的情绪，种成一座记忆花园`
- Tone: AI gentle companionship
- Buttons: `开始记录今天` and `进入 Memory Garden`
- Navigation: `Home`, `Memory Garden`, `About`
- Visual direction: dark night garden, dream particles, healing watercolor, glassmorphism
- Desktop landscape first, with responsive fallback
- Bottom centered localStorage status text
- No diagnosis boundary copy on Home for this version

## Source Documents

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `docs/requirements/project-requirements.md`
- `docs/requirements/user-stories.md`
- `frontend/README.md`
- User-provided PDF: `小学期项目.pdf`

`references/log-and-planning.md` is referenced by the workflow skill but is not present in the repository.

## Files Changed

- `frontend/package.json`
- `frontend/index.html`
- `frontend/postcss.config.js`
- `frontend/tailwind.config.js`
- `frontend/pnpm-lock.yaml`
- `frontend/pnpm-workspace.yaml`
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `docs/vibe-logs/log-07-home-demo.md`

## Key Decisions

- Implemented only the Home page, as requested.
- Added the missing Vite entry files because the frontend shell did not include `index.html` or `src/main.jsx`.
- Added Tailwind CSS because the current user request explicitly requires React + Vite + Tailwind CSS.
- Kept AI, diary generation, garden cards, and past-self chat as future mock-only pages. No real AI API, backend route, database, login, or registration was added.
- Home navigation and CTA buttons use hash links to future routes: `#/ai-companion-chat`, `#/memory-garden`, and `#/about`.
- Home reads possible memory arrays from `localStorage` and displays a bottom status message. If no memories exist, it displays: `你的花园还很安静，从一次倾诉开始。`

## Architecture Notes

The existing design docs prefer Ant Design and TypeScript and say Tailwind CSS is not part of the first formal stack. This task is a pure frontend course demo request from the user and explicitly specifies Tailwind CSS. The implementation is therefore scoped as a frontend prototype layer and does not change backend/API/database architecture.

## Verification

- `pnpm install`: completed after approving the required `esbuild` build script and rebuilding it with the bundled Node runtime on PATH.
- `pnpm run build`: passed.
- Local dev server: `http://localhost:5173/`
- Desktop browser check: Home rendered with title, navigation, subtitle, CTA buttons, night garden background, and bottom localStorage status.
- Mobile browser check at 390px width: no horizontal overflow; title and buttons remain readable.

## Blockers or Risks

- `git fetch origin` failed twice with `Recv failure: Connection was reset`, so the branch was created from the current clean local `main`.
- Browser DOM snapshot inspection had a compatibility issue in the in-app browser, so visual verification used screenshots and read-only DOM evaluation instead.
- Only Home is implemented. Button targets point to future hash routes that will be implemented one page at a time after user confirmation.

## Next Requirement Plan

Before coding the next page, confirm the AI Companion Chat page details with the user:

- Page goal and whether it is text-first or image-upload-first.
- Chat layout, message style, input controls, and mock AI reply behavior.
- Buttons for sending, changing question, uploading image, and generating diary.
- What temporary conversation state should be saved in `localStorage`.
- Exact jump target after `我说完了，生成日记`.

Acceptance proof for the next page should include a successful build, desktop and mobile visual checks, and a mock flow showing at least one user message and one AI companion reply.
