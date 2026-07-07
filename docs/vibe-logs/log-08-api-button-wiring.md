# Log 08 - API Button Wiring

## Date and Branch

- Date: 2026-07-07
- Branch: `frontend/home-demo`

## User Request

根据现有的后端 API 接口，把现有页面 button 对接上去；如果缺少对应的 API，写进本次 vibe log。

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `docs/requirements/project-requirements.md`
- `frontend/README.md`
- `backend/README.md`

Note: `innergarden-agent-workflow` 要求读取 `references/log-and-planning.md`，但当前仓库不存在该文件。本日志按 skill 中列出的必填项补齐。

## Files Changed

- `frontend/vite.config.js`
- `frontend/src/api/client.js`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `docs/vibe-logs/log-08-api-button-wiring.md`

## Real Backend APIs Wired

- `GET /api/v1/health`
  - About 页“检查后端健康状态”按钮调用。
- `POST /api/v1/auth/login`
  - 前端 demo session 会先尝试登录 `demo@innergarden.local`。
- `POST /api/v1/auth/register`
  - 如果 demo 用户不存在，自动注册一个课程演示用户。
- `GET /api/v1/auth/me`
  - 如果本地已有 token，先校验当前登录态。
- `POST /api/v1/entries`
  - AI Companion Chat 页“发送”按钮调用，用用户输入创建 entry，并读取后端返回的情绪分析和日记草稿。
- `POST /api/v1/diaries`
  - Diary Result 页“保存到 Memory Garden”按钮调用，把可编辑日记保存为真实 diary。
- `GET /api/v1/diaries`
  - Memory Garden 页加载真实日记列表。
- `GET /api/v1/diaries/{diary_id}`
  - Memory Detail 页读取真实日记详情。
- `GET /api/v1/stats/overview`
  - Memory Garden 页读取真实统计数字。

## Missing APIs Kept as Mock

- `POST /api/v1/chat/messages`
  - 当前没有独立聊天消息保存和 AI 回复接口；“发送”临时映射到 `POST /api/v1/entries` 完成核心闭环。
- `POST /api/v1/chat/next-question`
  - “换个问题问我”仍使用本地 mock 追问文案。
- 图片上传和文件保存 API
  - “上传图片”只做浏览器本地预览，不会上传到后端。
- `POST /api/v1/diaries/generate`
  - 后端没有单独生成日记接口；当前使用 `POST /api/v1/entries` 返回的 draft diary。
- `/api/v1/memories`
  - 后端没有 memory card 列表、详情、删除资源；Memory Garden 当前使用真实 `diaries` 作为可回顾数据源。
- `/api/v1/memories/{id}/past-self-chat`
  - Memory Detail 页“和那天的我聊聊”仍使用本地 mock。
- 封面图生成、封面 prompt、图片历史 API
  - 当前没有后端接口，页面不做真实生成或保存。

## Key Decisions

- 不新增后端接口，避免超出本次“根据现有 API 对接”的范围。
- 所有前端 HTTP 请求集中到 `frontend/src/api/client.js`，页面不散写完整后端 URL。
- 使用 Vite dev proxy 把 `/api` 代理到 `http://localhost:8000`，保持前端代码中的 API base 为 `/api/v1`。
- 保留本地 mock 的位置都在页面状态文案中明确说明，并在本日志列为缺口。
- 当前分支原有 demo 使用 React + Vite + Tailwind CSS；本次不做技术栈重构，只做最小可联调改动。

## Verification

- Passed: `pnpm run build`
  - The first sandboxed attempt failed because the terminal could not find bundled Node.
  - The second sandboxed attempt reached Vite but esbuild child process launch was blocked by `EPERM`.
  - The approved build run completed successfully.
- Not run: backend tests, because this task did not change backend code. Existing backend API paths were inspected and consumed from the frontend only.

## Risks and Blockers

- 后端需要先运行在 `http://localhost:8000`，前端按钮才能真实联调。
- demo 用户自动注册依赖后端数据库允许创建 `demo@innergarden.local`。
- 当前 `memories`、图片上传、聊天追问、过去自我对话仍是产品需求中的缺失 API，需要后端后续补齐。
- `references/log-and-planning.md` 在当前仓库缺失，skill 中对应的附加日志规则无法读取。

## Next Requirement Plan

1. Product: 在 `docs/requirements/project-requirements.md` 中确认 memories 是否作为独立资源，或是否继续用 diaries 承载第一版 Memory Garden。
2. API: 如果坚持 Memory Garden 卡片模型，补充 `/api/v1/memories`、图片上传、past-self-chat 的请求和响应字段。
3. Backend: 在 FastAPI 中按现有分层实现缺失接口，并补齐权限校验和测试。
4. Frontend: 把当前 mock 的按钮替换为真实 API 调用，补充 loading、失败、空状态。
5. Proof: 运行前端 build、后端 API 测试，并用一条真实记录演示 Home -> Chat -> Diary -> Garden -> Detail 闭环。
