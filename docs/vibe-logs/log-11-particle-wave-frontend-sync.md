# Log 11 - Particle Wave Frontend Sync

## 日期与分支

- 日期：2026-07-08
- 分支：`frontend/particle-wave-sync`
- 基线：`origin/main`，已执行 `git fetch origin` 与 `git pull --ff-only origin main`，结果为 Already up to date

## 用户请求

按照 `innergarden-agent-workflow` skill，将 `C:\Users\Lenovo\particle-wave` 目录中的粒子波前端内容同步到 InnerGarden 的 `frontend` 部分；先阅读架构，再进行操作；日志使用中文编写。

## 已阅读的 Markdown 文档

- `README.md`
- `docs/design/system-architecture.md`
- `docs/design/technology-stack.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`
- `frontend/README.md`
- `docs/vibe-logs/log-10-backend-test-infrastructure.md`

说明：skill 要求的 `references/project-map.md` 与 `references/log-and-planning.md` 在仓库根目录和 skill 目录下均不存在，因此无法读取；本次日志记录该缺口。

## 变更文件

- `frontend/package.json`：新增 `three` 依赖。
- `frontend/pnpm-lock.yaml`：同步 Three.js 依赖锁定信息。
- `frontend/public/particle-wave-statue.jpg`：从源项目复制粒子采样图片资源。
- `frontend/src/components/ParticleWaveHero.jsx`：新增 React 版 Three.js 粒子波界面组件。

## 关键决策与架构约束

- 没有整包覆盖 `frontend`，而是把源项目的 DOM 直挂式 Three.js 代码改造成独立 React 组件，保持现有 InnerGarden 前端入口、页面结构和已写组件不变。
- Three.js 只作为视觉组件依赖引入，没有改变既有 React + Vite 架构，也没有新增后端 API 或数据库变更。
- `statue.jpg` 放入 `frontend/public/`，组件通过 `/particle-wave-statue.jpg` 引用，符合 Vite 静态资源访问方式。
- 按用户补充要求，本次不接入或修改已有页面，不生成粒子波界面以外的前端内容；后续由前端同学在需要的位置显式引用该组件。
- 组件在卸载时清理 animation frame、resize listener、OrbitControls、renderer、geometry 和 material，避免页面切换后残留 WebGL 资源。

## 验证命令与结果

```bash
cd frontend
pnpm run build
```

结果：构建成功。

结果：构建成功，主 JS 产物约 211.48 kB，未出现大 chunk 警告。由于 `ParticleWaveHero` 当前未接入已有页面，Three.js 没有进入现有页面 bundle；后续一旦接入，建议动态导入以控制体积。

## 阻塞与风险

- 初始系统 PATH 找不到 `git` 和 `node`，已改用 Codex bundled Git/Node 完成分支流程、依赖安装和构建。
- `pnpm add` 首次因 postinstall 找不到 `node` 失败，并生成临时 `.pnpm-store/`；该目录已清理。
- skill 引用的两个 references 文件不存在，日志与规划依据改用已读取的项目设计文档和现有 vibe log。
- Three.js 组件当前未接入已有页面；如果后续需要展示，需要在不破坏现有组件边界的前提下接入，并建议懒加载。

## 下一步需求计划

- 产品：在 `docs/requirements/project-requirements.md` 中明确首页是否需要 3D 记忆视觉，以及它和情绪日记闭环的验收标准。
- 前端：在明确需求后选择接入位置；接入时优先动态导入 `ParticleWaveHero`，并避免改动无关已有组件。
- 后端：无需为本次视觉同步新增接口；继续保持 `/api/v1/entries`、`/api/v1/diaries`、`/api/v1/stats` 作为主闭环数据源。
- 数据库：本次无数据库变更。
- 测试：补一个轻量前端渲染测试或 Playwright 截图检查，证明首页 canvas 非空且移动端不遮挡按钮。
- 演示：在 defense 或演示材料中补充首页粒子波效果截图，并说明其来源于用户情绪记忆的可视化表达。
