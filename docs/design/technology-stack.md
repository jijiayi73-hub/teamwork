# Technology Stack

本文档是 Inner Garden 的技术栈定稿，用于约束 AI coding 和人工开发。目标是让任何开发者在开工前读完本文后，不会误用框架、混乱接口风格，或让数据库结构一轮一变。

实现前必须同时阅读：

- `docs/design/system-architecture.md`
- `docs/design/api-design.md`
- `docs/design/database-design.md`

## 1. 技术栈总表

| 层级 | 固定选择 | 用途 | 不使用 |
| --- | --- | --- | --- |
| 前端框架 | React + TypeScript | 页面、组件和类型约束 | Vue、Angular、Svelte、Next.js |
| 构建工具 | Vite | 本地开发和前端构建 | Webpack 手写配置、Create React App |
| 路由 | React Router | 前端页面路由 | 自写路由、服务端页面路由 |
| HTTP 客户端 | Axios | 统一请求封装和拦截器 | 页面中散写 fetch |
| 状态管理 | Zustand | 用户信息、token、跨页面状态 | Redux、MobX、复杂状态机 |
| UI 组件 | Ant Design | 表单、按钮、表格、弹窗、布局 | Material UI、Bootstrap、Tailwind UI |
| 图表 | ECharts | 趋势图、分布图、统计图 | D3 手写复杂图表、Chart.js |
| 后端框架 | FastAPI | REST API、OpenAPI 文档 | Flask、Django、Node.js、Express |
| 后端语言 | Python 3.11+ | 服务端实现 | Java、Go、Node.js 后端 |
| 数据校验 | Pydantic | 请求响应 Schema | 手写 dict 校验 |
| ORM | SQLAlchemy 2 | 数据库模型和查询 | 裸 SQL、Peewee、Django ORM |
| 迁移 | Alembic | 数据库结构变更 | 手动改库不留记录 |
| 数据库 | SQLite | 课程演示和本地开发 | MongoDB、Redis、向量数据库 |
| 认证 | JWT + bcrypt | 登录态和密码安全 | 明文密码、session-only |
| 服务运行 | Uvicorn | FastAPI 本地服务 | Gunicorn 作为第一版必需项 |
| 后端测试 | Pytest + FastAPI TestClient | API 和业务测试 | 只靠手动点页面 |
| 前端测试 | Vitest | 前端逻辑测试 | Jest 混搭 |
| AI 接入 | Provider 抽象层 | 统一模型调用 | 业务代码直接依赖某家 SDK |
| 语音输入 | Browser MediaRecorder + 后端 STT | 录音上传和语音转文字 | 前端直接保存分析结果 |

## 2. 选择理由

### React + TypeScript + Vite

适合快速完成课程项目页面，也能通过 TypeScript 降低接口字段写错的概率。Vite 启动快，配置简单，不需要引入 Next.js 这类服务端渲染框架。

### Ant Design

项目需要登录、表单、列表、统计卡片、管理员表格和弹窗确认。Ant Design 能直接覆盖这些后台和应用型界面，减少自造 UI 组件导致的样式不一致。

### Axios

Axios 用于统一处理 base URL、JWT token、超时、错误响应和 401 退出。所有请求都集中在 `frontend/src/api/`，避免页面里散落 API 地址。

### Zustand

第一版只需要管理用户信息、token、少量跨页面状态。Zustand 比 Redux 更轻，不需要额外样板代码。

### ECharts

情绪趋势、情绪分布、统计面板是课程演示重点。ECharts 对折线图、柱状图、饼图和响应式渲染支持稳定，前端只接收后端统计数据并渲染。

### FastAPI + Pydantic

FastAPI 自动生成 Swagger 文档，适合前后端联调。Pydantic 可以固定请求和响应结构，避免接口字段随实现漂移。

### SQLAlchemy 2 + Alembic

SQLAlchemy 让业务代码不依赖 SQLite 方言，后续如果迁移 PostgreSQL，只需调整连接和少量字段类型。Alembic 保留数据库变更历史，避免手动改库导致每个人结构不同。

### SQLite

SQLite 足够支撑课程演示、单机开发和核心功能闭环。第一版使用 SQLite 可以减少部署和联调成本。不要为了“看起来高级”引入 PostgreSQL、MongoDB 或 Redis。

### AI Provider 抽象层

AI 是核心能力，但业务代码不能绑死某一个模型供应商。Provider 层统一暴露 `analyze_entry`、`generate_diary`、`generate_report` 等入口，service 层只处理结构化结果。

## 3. 前端实施规则

必须遵守：

- 使用 `.tsx` 和 `.ts` 编写新前端代码。
- 页面放在 `frontend/src/pages/`。
- 可复用组件放在 `frontend/src/components/`。
- API 请求放在 `frontend/src/api/`。
- 类型定义放在 `frontend/src/types/`。
- 用户登录态和 token 放在 Zustand store。
- 图表组件使用 ECharts。
- 表单、表格、弹窗、消息提示优先使用 Ant Design。

禁止：

- 在页面组件中直接写完整 URL。
- 同一个接口在多个文件里重复封装。
- 前端自己计算情绪风险等级。
- 前端自己拼接 AI prompt。
- 新增第二套 UI 组件库。

## 4. 后端实施规则

必须遵守：

- 新接口放在 `backend/app/api/v1/`。
- 新请求和响应模型放在 `backend/app/schemas/`。
- 业务流程放在 `backend/app/services/`。
- 数据库读写放在 `backend/app/repositories/`。
- 表结构放在 `backend/app/models/`。
- 通用鉴权依赖放在 `backend/app/core/`。
- AI 和语音供应商封装放在 `backend/app/providers/`。

禁止：

- Router 里直接写复杂业务流程。
- Router 或 Service 里拼接裸 SQL。
- 返回未经过 Schema 整理的 ORM 对象。
- 为了某个页面临时新增不符合 REST 风格的接口。
- 在业务代码里直接 import 某个模型供应商 SDK 并调用。

## 5. API 实施规则

API 固定规则：

- Base path：`/api/v1`
- 本地地址：`http://localhost:8000/api/v1`
- 文档地址：`http://localhost:8000/docs`
- 字段命名：snake_case
- 时间格式：ISO 8601
- 分页参数：`page`、`page_size`
- 认证头：`Authorization: Bearer <access_token>`

资源命名固定使用复数：

- `/auth/register`
- `/auth/login`
- `/auth/me`
- `/entries`
- `/diaries`
- `/stats/overview`
- `/stats/emotion-trend`
- `/stats/emotion-distribution`
- `/reports`
- `/admin/users`
- `/admin/stats`

同一个资源不允许出现多套别名。例如日记统一使用 `diaries`，不要混用 `journal`、`logs`、`records`。

## 6. 数据库实施规则

数据库固定规则：

- 第一版只使用 SQLite。
- 只通过 SQLAlchemy 访问数据库。
- 表结构以 `database-design.md` 为准。
- 结构变更必须同步 Alembic migration。
- 演示初始化必须同步 `data/init.sql` 和 `data/seed.sql`。

核心表固定为：

- `users`
- `entries`
- `emotion_analyses`
- `diaries`
- `reports`

禁止：

- 随意新增同义表，例如 `journals`、`moods`、`analysis_results`。
- 把 AI 分析字段塞进 `diaries` 后删除 `emotion_analyses`。
- 把原始输入字段塞进 `diaries` 后删除 `entries`。
- 用 JSON 大字段替代已经明确的结构化列。
- 让 AI 生成新的枚举值后直接入库。

## 7. AI 输出规则

AI 情绪分析输出固定为结构化 JSON。至少包含：

```json
{
  "title": "string",
  "diary_content": "string",
  "primary_emotion": "joy",
  "secondary_emotions": ["calm"],
  "valence": 0.5,
  "arousal": 0.4,
  "emotion_score": 75,
  "intensity": 0.6,
  "summary": "string",
  "suggestion": "string",
  "risk_level": "low",
  "risk_reason": "string"
}
```

固定语义：

- `emotion_score` 是情绪正向程度，不是焦虑程度。
- `emotion_score` 范围为 0 到 100。
- `emotion_score = 50` 表示中性。
- `risk_level` 只能是 `low`、`medium`、`high`。
- `primary_emotion` 必须来自 `database-design.md` 的固定枚举。

## 8. 第一版不引入

第一版不引入以下内容：

- Next.js
- Tailwind CSS
- Redux
- GraphQL
- WebSocket
- Redis
- Celery
- Docker Compose 多容器
- Kubernetes
- LangGraph
- RAG
- 向量数据库
- MongoDB
- 自训练情绪模型
- 微服务拆分

这些内容不是永远不能用，而是第一版不需要。若确实要引入，必须先更新设计文档并说明收益大于联调成本。

## 9. AI Coding Prompt 建议

给 AI coding 下任务前，可以先附上这段约束：

```text
Before coding, read docs/design/technology-stack.md, docs/design/system-architecture.md, docs/design/api-design.md, and docs/design/database-design.md.
Follow the fixed stack: React + TypeScript + Vite + Ant Design + ECharts + Axios + Zustand; FastAPI + Pydantic + SQLAlchemy 2 + Alembic; SQLite; JWT + bcrypt.
Do not introduce another framework, API style, database, table design, or AI output schema unless the design docs are updated first.
```

## 10. 变更批准标准

只有满足以下条件时，才能改变技术栈或核心设计：

- 当前技术无法实现课程验收所需功能。
- 替代方案能明显降低复杂度或修复关键风险。
- 已同步更新 `technology-stack.md`、`system-architecture.md`、`api-design.md` 或 `database-design.md`。
- 已说明对前端、后端、数据库、测试、演示数据的影响。

否则，不改变技术栈。
