# Log 09 - AI Companion Chat Page

## Date and Branch

- Date: 2026-07-07
- Branch: `frontend/home-demo`

## User Request

根据用户确认的第二页细节制作 AI Companion Chat 页面：页面中心是简洁的毛玻璃对话框，背景可使用上传图片本地预览，没有上传时保留首页梦核背景；AI 回复像手机消息通知一样竖向弹出；输入区合并图片、文字和语音入口；保留“我说完了，生成日记”并跳转到 `#/diary-result`。

## Source Docs Read

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `docs/requirements/project-requirements.md`
- `docs/requirements/user-stories.md`
- `frontend/README.md`
- `docs/vibe-logs/log-08-api-button-wiring.md`

Note: `references/log-and-planning.md` 仍不存在，本次日志按 `innergarden-agent-workflow` 中列出的必填项记录。

## Files Changed

- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `docs/vibe-logs/log-09-ai-companion-chat-page.md`

## Key Decisions and Architecture Constraints

- 保留上一轮已接入的 `POST /api/v1/entries`，用户发送文字时仍优先调用真实后端生成 entry 和 draft diary。
- 不新增后端接口，不接真实 AI API，不写 API key。
- 上传图片只用 `FileReader` 转为本地预览，并作为页面背景和本地草稿字段保存；不上传后端。
- 语音输入优先使用浏览器本地 Web Speech API；浏览器不支持时填入一段 mock 文本，保持演示流程可继续。
- 用户消息不作为气泡展示，页面只显示 AI 温柔回应的通知式卡片，符合用户确认的第二页交互。
- “换个问题问我”已移除，因为本页定位改为陪伴引导，不做提问式聊天。
- “我说完了，生成日记”保留为对话框底部居中的小字按钮，跳转 `#/diary-result`。

## Implemented Details

- 页面标题改为“今天想记录什么？”。
- 副文案使用“亦言亦思皆为序章”。
- 初始 AI 文案为“慢慢说，我在听。今天发生了什么？”。
- 输入框 placeholder 使用“慢慢说，我在听。今天发生了什么？”。
- 上传图片按钮、语音按钮、发送按钮合并到同一条输入框中，上传按钮不显示文字。
- AI 回复改为竖向 notification 样式，并加入轻微上浮出现动画。
- 图片上传后成为模糊、低饱和、夜晚梦核背景。
- 如果真实后端暂时失败，会生成本地 mock draft，保证可以继续进入 Diary Result。

## Missing APIs / Mocked Behavior

- 图片上传和文件保存 API 缺失：当前只做本地预览和本地草稿保存。
- 后端语音转文字 API 缺失：当前只用浏览器本地语音识别或 mock 文本。
- 独立聊天消息 API 缺失：当前仍用 `POST /api/v1/entries` 承载核心文字输入闭环。

## Verification

- Passed: `pnpm run build`
  - Sandboxed run was blocked by esbuild `EPERM`.
  - Approved build run completed successfully.

## Risks and Blockers

- Web Speech API 在不同浏览器兼容性不一致，因此语音功能只能作为本地演示增强，不能视为稳定后端能力。
- 本地图片以 data URL 存在草稿里，适合 demo，不适合长期数据库保存。
- 后端不可用时的 local mock 草稿可以进入 Diary Result，但保存到真实 Memory Garden 仍依赖后端 diary 接口。

## Next Requirement Plan

1. Product: 确认 Diary Result 页是否继续保留情绪选择、情绪底色和封面预览。
2. Frontend: 在用户确认后制作第三页 Diary Result / Mood Check-in，读取第二页保存的 draft 和 image preview。
3. Backend: 后续补图片上传、语音转文字、聊天消息保存接口时，再替换当前本地 mock。
4. Proof: 第三页完成后用一条文字输入和一张图片演示 Chat -> Diary Result 的完整跳转。
