# API Design

本文档作为 Inner Garden 的 API 与技术实现指导，统一前后端、数据库、AI 与测试的设计边界。实现时优先遵循本文的约定，避免技术栈反复变更导致联调成本上升。

## 实现状态

**已实现**：
- 用户认证 (User, Entry, EmotionAnalysis, Diary)
- 统计接口 (Stats)
- 管理员接口 (Admin)
- RAG Chat 接口 (Conversation, Message, MessageSource)
- Memory Cards 接口 (MemoryCard, UploadedAsset, Past Self Chat)
- 图片上传接口 (Image Upload with static file serving)

**规划中，尚未实现**：
- 周期报告功能 (Report) - 文档中保留 generate_report 接口设计，但后端尚未实现
- 语音转文字接口 (Speech) - 第二优先级，前端支持 MediaRecorder 录音

## 1. 最终技术栈

前端统一采用 React、TypeScript、Vite、React Router、Axios、Zustand、Ant Design 和 ECharts。前端职责是页面展示、状态管理、表单交互、路由切换和图表渲染，不承载业务计算逻辑。

后端统一采用 Python 3.11+、FastAPI、Pydantic、SQLAlchemy 2、Alembic 和 Uvicorn。后端负责鉴权、业务编排、AI 调用、数据持久化与统计聚合，所有接口都返回 JSON。

开发与课程演示阶段数据库使用 SQLite，所有数据库访问统一通过 SQLAlchemy 完成。后续如果切换到 PostgreSQL，只需要替换连接配置，不修改业务代码。认证统一采用 JWT 和 bcrypt。

AI 模块必须通过统一 Provider 层接入，业务代码不得直接依赖某一家模型供应商。语音输入使用浏览器 MediaRecorder 录音后上传，后端再做语音转文字。图表交互统一由后端统计接口提供数据，前端只负责渲染。

## 2. 项目闭环

核心业务闭环如下：用户输入文字或语音，后端接收原始内容，AI 完成日记整理与情绪分析，用户确认或编辑后写入数据库，再由历史日记、周报/月报和趋势图形成长期回顾能力。

这个闭环要同时覆盖课程要求中的前后端分离、JSON 返回、至少两类关联数据、登录和角色区分、动态数据可视化，以及 AI 参与核心业务并保存结果。

## 3. 全局 API 规范

基础路径统一为 /api/v1，本地开发地址为 http://localhost:8000/api/v1，Swagger 文档由 FastAPI 自动提供在 /docs。

所有字段命名使用 snake_case，所有时间统一使用 ISO 8601 字符串，数据库内部建议保存 UTC，接口返回时带时区信息。分页统一使用 page 和 page_size，约束为 page >= 1 且 1 <= page_size <= 100。

统一成功响应建议包含 success、data、message 和 request_id。统一错误响应建议包含 success、error.code、error.message、error.details 和 request_id。认证头统一使用 Authorization: Bearer <access_token>。

角色仅区分 user 和 admin。后端必须做权限校验，不能只通过前端隐藏按钮实现权限控制。

## 4. 核心数据模型

建议至少保留以下核心数据：User、Entry、EmotionAnalysis、Diary、MemoryCard、Report。它们分别承载用户身份、原始输入、AI 分析结果、整理后的日记、可视化记忆卡片以及日报、周报或月报。

User 用于登录、角色区分和状态控制。Entry 记录用户原始输入，支持 text 和 voice 两种输入类型。EmotionAnalysis 保存 AI 输出，包含主情绪、次情绪、情绪分数、唤醒度、效价、风险等级、摘要和建议。Diary 绑定 Entry 和 EmotionAnalysis，保存最终确认后的日记正文。Report 用于周期性统计和趋势回顾。

情绪标签、风险等级、报告类型、用户状态和分析任务状态都应使用固定枚举，不允许 AI 自由创造标签，避免统计口径失真。

## 5. AI 设计原则

AI 能力必须经过统一服务层封装，建议提供 analyze_entry、generate_diary、generate_report 和 generate_image_prompt 等稳定入口。业务层只处理结构化结果，不直接拼接模型请求。

AI 的情绪分析输出必须是固定 JSON Schema，重点字段包括 title、diary_content、primary_emotion、secondary_emotions、valence、arousal、emotion_score、intensity、summary、suggestion、risk_level 和 risk_reason。这样可以降低模型输出漂移，便于入库和前端展示。

emotion_score 的语义应保持为情绪正向程度，范围 0 到 100，其中 50 表示中性。不要把它定义成焦虑程度，否则图表和统计的语义会混乱。风险等级只允许 low、medium 和 high。

## 6. 推荐目录结构

前端建议采用 api、components、pages、routes、stores、types、hooks 和 utils 的结构，将请求封装、组件、页面、路由和状态隔离。

后端建议采用 api/v1、schemas、models、repositories、services、core 和 database 的结构。API 层负责接收请求，schemas 负责校验与响应，services 负责业务编排，repositories 负责数据读写，core 负责配置、鉴权和通用工具。

## 7. 第一阶段必须完成的接口

第一阶段优先完成注册、登录、当前用户信息、快速创建并分析 Entry、日记的增查改删、首页统计、情绪趋势、情绪分布、Memory Card CRUD、图片上传和 Past Self Chat，以及管理员用户列表和管理员统计接口。

这一阶段完成后，已经可以满足课程验收里最关键的功能闭环：登录和角色区分、AI 深度集成、数据持久化、增查改删以及动态趋势图。

## 8. API 设计优先级

系统健康检查、认证、Entry 快速分析、Diary 保存、Stats 聚合和 Admin 基础统计属于第一优先级。

语音转文字、日历热力图、报告生成属于第二优先级，用于增强体验。

封面图生成、分享卡片、日记对话和分析反馈属于第三优先级，属于加分项，不应阻塞主闭环。

## 9. 前端 API 文件拆分

前端请求层建议按业务拆分为 client.ts、auth.ts、users.ts、entries.ts、speech.ts、diaries.ts、analyses.ts、stats.ts、reports.ts、conversations.ts、memories.ts、files.ts 和 admin.ts。

其中 client.ts 只负责基础 URL、JWT 注入、超时、统一错误解析和 401 自动退出，其他文件只负责具体业务接口，避免请求逻辑分散到页面中。

## 10. 测试与工程工具

后端至少补齐 Pytest 和 FastAPI TestClient 的接口测试。前端建议使用 Vitest、ESLint 和 Prettier 保持代码一致性。课程要求稳定优先，因此第一阶段更应该投入到后端接口测试和核心流程测试上。

## 11. 明确不在第一版引入的内容

第一版不建议引入 LangGraph、复杂 Agent、RAG、向量数据库、WebSocket、微服务、Redis、Docker 多容器或自训练情绪模型。这些能力不会直接提升当前课程闭环，反而会增加失败点和联调复杂度。

## 12. 定案总结

最终执行方案建议固定为：前端 React + TypeScript + Vite + Ant Design + ECharts + Axios + Zustand；后端 Python + FastAPI + Pydantic + SQLAlchemy + Alembic；数据库 SQLite，保留迁移 PostgreSQL 的能力；认证 JWT + bcrypt；AI Provider 抽象层加结构化 JSON 输出；语音 MediaRecorder + 后端语音转文字；图表由后端统计接口驱动；接口风格统一为 RESTful、/api/v1、snake_case 和 ISO 8601；测试使用 Pytest 和 FastAPI TestClient。

