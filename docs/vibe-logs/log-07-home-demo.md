# Log 07 - Home Demo

## 日期与分支

- 日期：2026-07-07
- 分支：`frontend/home-demo`

## 用户请求

仅为"心灵情绪日记"的纯前端演示构建第一页。用户明确要求在编码前确认每个页面，避免后端/API/数据库/登录工作，使用本地 mock 数据和 `localStorage`，并在确认后仅实现 Home。

确认的 Home 细节：

- 主标题：`Mindful Memory Diary`
- 中文副标题：`把今天的情绪，种成一座记忆花园`
- 语气：AI 温柔陪伴
- 按钮：`开始记录今天` 和 `进入 Memory Garden`
- 导航：`Home`、`Memory Garden`、`About`
- 视觉方向：夜晚梦核花园、梦境粒子、治愈水彩、毛玻璃效果
- 优先桌面横向布局，响应式回退
- 底部居中 localStorage 状态文本
- 此版本的 Home 上无诊断边界文案

## 源文档

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `docs/requirements/project-requirements.md`
- `docs/requirements/user-stories.md`
- `frontend/README.md`
- 用户提供的 PDF：`小学期项目.pdf`

workflow skill 引用了 `references/log-and-planning.md`，但它不存在于仓库中。

## 变更文件

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

## 关键决策

- 按要求仅实现 Home 页面。
- 添加了缺失的 Vite 入口文件，因为 frontend 外壳不包含 `index.html` 或 `src/main.jsx`。
- 添加了 Tailwind CSS，因为当前用户请求明确要求 React + Vite + Tailwind CSS。
- 保持 AI、日记生成、花园卡片和过去自我对话为仅未来的 mock 页面。未添加真实 AI API、后端路由、数据库、登录或注册。
- Home 导航和 CTA 按钮使用哈希链接指向未来路由：`#/ai-companion-chat`、`#/memory-garden` 和 `#/about`。
- Home 从 `localStorage` 读取可能的记忆数组并显示底部状态消息。如果没有记忆，则显示：`你的花园还很安静，从一次倾诉开始。`

## 架构说明

现有设计文档偏好 Ant Design 和 TypeScript，并说明 Tailwind CSS 不是第一版正式技术栈的一部分。此任务是来自用户的纯前端课程演示请求，明确指定了 Tailwind CSS。因此实现范围限定为前端原型层，不改变后端/API/数据库架构。

## 验证

- `pnpm install`：在批准所需的 `esbuild` 构建脚本并使用 PATH 上的 bundled Node runtime 重新构建后完成。
- `pnpm run build`：通过。
- 本地开发服务器：`http://localhost:5173/`
- 桌面浏览器检查：Home 渲染了标题、导航、副标题、CTA 按钮、夜晚梦核背景和底部 localStorage 状态。
- 390px 宽度的移动浏览器检查：无横向溢出；标题和按钮保持可读。

## 阻塞与风险

- `git fetch origin` 两次失败，错误为 `Recv failure: Connection was reset`，因此从当前干净的本地 `main` 创建了分支。
- 浏览器 DOM 快照检查在应用浏览器中存在兼容性问题，因此视觉验证使用截图和只读 DOM 评估。
- 仅实现了 Home。按钮目标指向将在用户确认后逐页实现的未来哈希路由。

## 下一步需求计划

在编写下一页代码之前，与用户确认 AI Companion Chat 页面细节：

- 页面目标以及是文字优先还是图片上传优先。
- 聊天布局、消息样式、输入控制和 mock AI 回复行为。
- 发送、换个问题、上传图片和生成日记的按钮。
- 应在 `localStorage` 中保存什么临时对话状态。
- `我说完了，生成日记` 后的确切跳转目标。

下一页的验收证明应包括成功构建、桌面和移动视觉检查，以及显示至少一条用户消息和一条 AI 陪伴回复的 mock 流程。
