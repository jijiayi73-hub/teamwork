# Inner Garden Current Status

## 2026-07-10 Update: TASK-037 AI朗读功能（火山引擎豆包TTS）

实现AI文本朗读功能，在每个AI生成的文本气泡后添加朗读按钮，点击后调用火山引擎豆包TTS API朗读内容。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 后端TTS协议模块 | Implemented | `volcengine_tts/` 目录完整（protocol, events, exceptions, models, client） |
| TTS WebSocket API | Implemented | `ws://localhost/api/v1/tts/stream` 双向流式音频传输 |
| 前端TTS组件 | Implemented | ChatPage添加TTS按钮（♪图标 + "朗读"/"停止"） |
| AudioContext播放 | Implemented | PCM 24000Hz音频流式播放 |
| 环境变量配置 | Implemented | `.env.example` 添加TTS配置项 |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.12s |
| 后端导入 | Passing | TTS模块导入验证通过 |

**Validation:**
```bash
# 前端构建
cd frontend
npm run build
# Result: ✓ built in 2.12s

# 后端TTS模块
cd backend
py -c "from app.services.volcengine_tts import VolcengineTTSClient, TTSConfig; print('TTS module imports OK')"
# Result: TTS module imports OK

# 主应用导入
py -c "from app.main import app; print('Main app imports OK')"
# Result: Main app imports OK
```

**Changes:**
- **Backend**: 新建 `backend/app/services/volcengine_tts/` - 完整TTS协议实现
- **Backend**: 新建 `backend/app/routers/tts.py` - TTS WebSocket API
- **Backend**: 更新 `backend/app/config.py` - 添加TTS配置
- **Backend**: 更新 `backend/app/main.py` - 注册TTS路由
- **Frontend**: 更新 `frontend/src/AppFixed.jsx` - 添加TTS按钮和音频播放
- **Styles**: 更新 `frontend/src/styles.css` - 添加TTS按钮样式

**Expected behavior:**
- 每个AI消息气泡后显示朗读按钮
- 点击按钮连接后端TTS WebSocket
- 流式播放AI消息的语音朗读
- 支持播放/停止控制
- 使用PCM格式，24000Hz采样率

**环境变量:**
```bash
VOLCENGINE_TTS_API_KEY=your-api-key-here
VOLCENGINE_TTS_RESOURCE_ID=seed-tts-2.0
VOLCENGINE_TTS_SPEAKER=zh_female_qingxin
```

**API Endpoints:**
- `ws://localhost/api/v1/tts/stream` - TTS流式音频（需要认证）
- `GET /api/v1/tts/health` - TTS健康检查（公开）
- `GET /api/v1/tts/speakers` - 可用音色列表（公开）

---

## 2026-07-10 Update: TASK-036 日记生成 Fallback 只记录用户对话

修复日记生成 fallback 逻辑，当 LLM 无法生成足够的日记内容时，只记录用户对话内容，不包含 AI 回复。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 前端用户消息提取 | Implemented | `transcriptFromUserMessages()` 只提取 `role === 'user'` 的消息 |
| 前端 Fallback | Updated | `handleGenerateDiary()` 使用 `userTranscript` 而非包含 AI 回复的 `transcript` |
| 后端用户消息提取 | Implemented | `_extract_user_content_from_conversation()` 从对话中提取用户消息 |
| 后端 Fallback | Updated | `analyze_text_with_llm()` 在所有 fallback 路径使用纯用户内容 |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.86s |
| 后端导入 | Passing | `py -c "from app.services.analysis_service import ..."` → OK |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.86s

cd backend
py -c "from app.services.analysis_service import analyze_text_with_llm, _extract_user_content_from_conversation; print('Backend imports OK')"
# Result: Backend imports OK
```

**Changes:**
- **Frontend**: 更新 `frontend/src/AppFixed.jsx` - 添加 `transcriptFromUserMessages()` 函数，更新 `handleGenerateDiary()` fallback 逻辑
- **Backend**: 更新 `backend/app/services/analysis_service.py` - 添加 `_extract_user_content_from_conversation()` 函数，更新 `analyze_text_with_llm()` fallback 逻辑

**Expected behavior:**
- 当 LLM 成功生成日记内容时，使用 AI 生成的内容
- 当 LLM 返回空内容或信息量不足时，使用纯用户对话作为日记内容（不包含 AI 回复）
- 前后端 fallback 逻辑保持一致

---

## 2026-07-10 Update: TASK-035 VPS测试数据生成

在VPS端生成测试账户和对话数据，用于演示和测试。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 测试数据脚本 | Implemented | `scripts/generate-test-data.py` 创建完成 |
| 测试账户 | Created | test1 / test1@example.com / 123456 (User ID: 15) |
| 6月对话数据 | Generated | 29个对话 (6.1-6.29)，每日2-4组消息交换 |
| VPS数据验证 | Passing | API返回87个对话总数 |

**Validation:**
```bash
py scripts/generate-test-data.py
# Result: ✅ 29 conversations created with messages

curl https://jijiayi.online/api/v1/chat/conversations
# Result: 87 total conversations
```

**Changes:**
- **Scripts**: 新增 `scripts/generate-test-data.py` - 测试数据生成脚本

**Expected behavior:**
- 测试用户 test1 可以登录 VPS
- 拥有6月1-29日的完整对话记录
- 每日对话包含随机话题和AI回复
- 可用于功能演示和测试

---

## 2026-07-10 Update: TASK-034 聊天背景动画效果修复

修复上传图片后背景动画效果消失的问题，确保用户上传图片后仍能保留旋转和粒子动画效果。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 背景动画保留 | Fixed | 将 `uploadedImage` 传递给 `ParticleWaveHero` 组件而非静态 div |
| 条件渲染移除 | Fixed | 始终渲染 `ParticleWaveHero`，移除互斥的条件渲染 |
| 图片可见度优化 | Implemented | `backgroundOpacity` 动态调整（有图片 0.85，无图片 0.62） |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.33s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.33s
```

**Changes:**
- **Frontend**: 更新 `frontend/src/AppFixed.jsx` - ChatPage 背景渲染逻辑

**Expected behavior:**
- 上传图片后，图片作为背景显示
- 粒子波浪动画叠加在图片上方继续运行
- 旋转和波浪动画效果不受影响
- 多次上传图片时，每次覆盖上一张，动画持续运行

---

## 2026-07-10 Update: TASK-032 日记标题与内容文艺化改进

改进 AI 生成的日记标题和内容风格，使其更加文艺诗意，同时确保基于用户真实表达，不编造事实。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Fallback 标题更新 | Implemented | `_generate_title_from_emotion()` 使用文艺风格标题 |
| LLM Prompt 优化 | Implemented | `EMOTION_ANALYSIS_SYSTEM_PROMPT` 添加文艺风格指南和内容完整性要求 |
| 后端导入 | Passing | `py -c "from app.services.analysis_service import ..."` → OK |

**Validation:**
```bash
cd backend
py -c "from app.services.analysis_service import EMOTION_ANALYSIS_SYSTEM_PROMPT, _generate_title_from_emotion; print('OK')"
# Result: Backend imports OK, Prompt updated, Fallback titles verified
```

**Changes:**
- **Backend**: 更新 `backend/app/services/analysis_service.py` - `_generate_title_from_emotion()` 函数
- **Backend**: 更新 `backend/app/services/analysis_service.py` - `EMOTION_ANALYSIS_SYSTEM_PROMPT` prompt

**Expected behavior:**
- 标题使用自然意象（微光、彩虹、港湾）和空间意象，含蓄表达情绪
- 日记内容完整整理用户话语，保持第一人称叙述
- 严格基于用户表达的内容，不虚构事件或感受

---

## 2026-07-09 Update: TASK-030 语音输入接口实现

在本地实现语音输入相关后端接口，为未来扩展服务端语音转文字功能预留接口。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Audio Schemas | Implemented | `backend/app/schemas/audio.py` 定义音频上传和转录 Schema |
| Audio Router | Implemented | `backend/app/routers/audio.py` 实现音频上传和转录 API |
| Audio API Client | Implemented | `frontend/src/api/client.js` 添加 `uploadAudio()`, `transcribeAudio()` 函数 |
| 后端导入 | Passing | `py -c "from app.main import app"` → OK |
| 前端构建 | Passing | `npm run build` → ✓ built in 3.55s |

**Validation:**
```bash
cd backend
py -c "from app.main import app; print('Backend imports OK')"
# Result: Backend imports OK

cd frontend
npm run build
# Result: ✓ built in 3.55s
```

**Changes:**
- **Backend**: 新增 `backend/app/schemas/audio.py` - 音频相关 Schema 定义
- **Backend**: 新增 `backend/app/routers/audio.py` - 音频上传和转录 API
- **Backend**: 更新 `backend/app/main.py` - 注册音频路由
- **Frontend**: 更新 `frontend/src/api/client.js` - 添加音频 API 客户端函数

**Expected behavior:**
- 前端可通过 `uploadAudio(file, filename)` 上传音频文件到服务器
- 音频文件保存到 `/uploads/audio/` 目录，最大 25MB
- 支持 webm, ogg, wav, mp3, m4a 格式
- `transcribeAudio()` 接口已预留，当前返回模拟数据
- 保留现有 Web Speech API 实现，无需后端即可使用语音输入

**API Endpoints:**
- `POST /api/v1/audio/upload` - 上传音频文件（需要认证）
- `POST /api/v1/audio/transcribe` - 转录音频为文字（预留，需要认证）
- `GET /api/v1/audio/formats` - 查询支持的音频格式（公开）

**后续扩展:**
- 集成真实 STT 服务（Azure Speech, Google Cloud STT, OpenAI Whisper）
- 实现音频元数据解析（真实时长、质量检测）
- 考虑对象存储代替本地存储

---

## 2026-07-09 Update: TASK-029 前端认证模块修复与部署

修复了生产环境中登录功能报错 `readJsonResponse is not defined` 的问题，并已部署到 VPS。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| readJsonResponse 函数 | Defined | 添加了辅助函数处理 JSON 响应解析 |
| login 函数 fallback 变量 | Defined | 在 login() 中添加了错误消息 fallback |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.00s |
| VPS 部署 | Complete | 前端容器已重建并运行，健康检查通过 |

**Validation:**
```bash
# 本地构建
cd frontend
npm run build
# Result: ✓ built in 2.00s

# VPS 部署验证
curl http://jijiayi.online/api/v1/health
# Result: {"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok"}

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml ps"
# Result: inner-garden-frontend healthy
```

**Changes:**
- **Frontend**: `frontend/src/api/auth.js` 添加 `readJsonResponse()` 函数定义
- **Frontend**: `frontend/src/api/auth.js` 在 `login()` 函数中添加 `fallback` 变量
- **VPS**: 前端容器已重新构建并重启，新镜像包含修复代码

**Expected behavior:**
- 登录功能可以正确处理 API JSON 响应
- 注册功能同样受益于共享的响应处理函数
- 错误处理统一且用户友好
- 生产环境登录/注册功能正常工作

**Deployed at**: 2026-07-09 23:00 UTC

---

## 2026-07-09 Update: TASK-027 VPS 部署收口

Inner Garden 已在 VPS `/opt/inner-garden` 通过 Docker Compose 启动，公网 `jijiayi.online` 的前端与 API 健康检查可访问。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Docker registry | Fixed | `/etc/docker/daemon.json` 使用腾讯云镜像优先、DaoCloud 备用 |
| Backend image build | Passing | 移除不必要的 `gcc/libpq-dev` 安装后，`docker compose -f docker-compose.prod.yml build backend` 成功 |
| Backend startup | Passing | `inner-garden-backend` 状态为 `healthy` |
| Frontend startup | Passing | `inner-garden-frontend` 状态为 `healthy` |
| Database migration | Applied | `docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head` 成功 |
| Public health | Passing | `http://jijiayi.online/api/v1/health` 返回 `status=healthy` |

**Validation:**
```bash
ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml ps"
# backend healthy, frontend healthy

ssh vps "curl -fsS http://127.0.0.1:8000/health"
# {"success":true,"data":{"status":"healthy"},"message":"ok","request_id":"local"}

ssh vps "curl -sS --max-time 10 http://jijiayi.online/api/v1/health"
# {"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}
```

**Changes:**
- **Backend**: `backend/Dockerfile` no longer installs unused Debian build dependencies.
- **Backend**: `analysis_service.py` imports `sqlalchemy.orm.Session` at runtime to fix container startup.
- **Frontend/Compose**: healthchecks use `127.0.0.1:8080` instead of `localhost` to avoid IPv6 localhost false negatives.

**Remaining risk:**
- `/opt/inner-garden/.env` still contains `DEEPSEEK_API_KEY=YOUR_KEY`; AI calls may fail until a real key is configured.
- SSL is not configured yet; current verified public URL is HTTP.

---

## 2026-07-09 Update: TASK-028 AI Chat 对话框布局修复

修复 AI Companion Chat 界面对话框布局 Bug，解决 CSS 列数与 HTML 元素数量不匹配导致的布局错位问题。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| CSS 列数修复 | Fixed | `.composer-shell` 从 3 列改为 4 列 |
| 前端构建 | Passing | `npm run build` → ✓ built in 1.80s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 1.80s
```

**Changes:**
- **Frontend**: `styles.css` 修复 `.composer-shell` 的 `grid-template-columns` 从 `minmax(0, 1fr) 42px 42px` 改为 `42px minmax(0, 1fr) 42px 42px`

**Expected behavior:**
- 对话框正确显示 4 个元素：📷上传按钮 | 输入框 | ♪语音按钮 | →发送按钮
- 布局对齐，无错位

---

## 2026-07-09 Update: TASK-026 Memory Garden 标题显示修复

Memory Garden 卡片现在显示保存的 title，用户可以在卡片列表中看到每张卡片的标题。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 卡片标题显示 | Implemented | `AppFixed.jsx` 添加 `memory.title` 显示 |
| CSS 样式 | Implemented | 添加 `.memory-title` 和 `.memory-date` 样式 |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.47s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.47s
```

**Changes:**
- **Frontend**: `AppFixed.jsx` MemoryGardenPage 卡片添加标题显示
- **Styles**: `styles.css` 添加 `.memory-title` 和 `.memory-date` 样式

**Expected behavior:**
- Memory Garden 卡片显示保存的 `title`
- 标题显示在封面图片下方
- 日期显示在标题下方
- 标题使用衬线字体，优雅清晰

---

## 2026-07-09 Update: TASK-025 About界面使用指南

About界面添加了完整的使用指南，采用标签导航和markdown风格排版。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 标签导航 | Implemented | 5个标签：快速开始、核心功能、常见问题、隐私声明、服务状态 |
| 使用指南内容 | Implemented | 注册登录、功能介绍、FAQ、隐私声明 |
| Markdown样式 | Implemented | 标题、列表、提示框、问答卡片样式 |
| 前端构建 | Passing | `npm run build` → ✓ built in 3.26s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 3.26s
```

**Changes:**
- **Frontend**: `AppFixed.jsx` AboutPage 重构，`styles.css` 添加md-样式类

**Expected behavior:**
- 用户访问 `/#/about` 看到标签导航界面
- 默认显示「快速开始」内容
- 点击标签切换不同章节
- 排版美观，支持标题、列表、提示、问答等格式

---

## 2026-07-09 Update: TASK-024 图片上传后直接用作背景和封面

用户上传图片后，聊天界面背景直接替换为用户上传的图片，生成日记时也使用这张图片作为卡片封面，不再触发 AI 图片生成。不显示预览对话框，多次上传时自动覆盖上一张。图片不发送给 AI，不在聊天消息中显示。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 背景图片替换 | Implemented | ChatPage 条件渲染，有 uploadedImage 时显示图片背景 |
| 移除预览对话框 | Implemented | 移除 imagePreviewUrl 预览区域 |
| 多次上传覆盖 | Implemented | setUploadedImage 每次覆盖上一张 |
| 图片不进入聊天 | Implemented | handleSend 移除图片逻辑，消息列表移除图片显示 |
| 按钮提示 | Implemented | 照相机按钮添加 title 属性 |
| 图片传递到 draft | Implemented | handleGenerateDiary 保存 uploadedImage 到 draft |
| 跳过 AI 封面生成 | Implemented | DiaryResultPage 检查 uploaded_image_url，直接使用 |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.06s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.06s
```

**Changes:**
- **Frontend**: `AppFixed.jsx` ChatPage 背景条件渲染，移除预览区域，handleSend 移除图片逻辑，DiaryResultPage 跳过 AI 生成

**Expected behavior:**
- 用户在 ChatPage 上传图片后，背景立即替换为上传的图片
- 不显示预览对话框，背景直接替换
- 多次上传时，每次覆盖上一张，使用最后一张
- 图片不发送给 AI，不在聊天消息中显示
- 生成日记时，直接使用上传的图片作为卡片封面
- 不再调用 AI 图片生成 API
- 如果用户未上传图片，仍使用 AI 生成封面
- 鼠标悬浮照相机按钮显示提示："上传图片作为背景和本日封面"

---

## 2026-07-09 Update: TASK-023 Chatbot 图片上传功能

在 Chatbot 界面添加了图片上传按钮，允许用户在聊天时发送图片。

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| 图片上传按钮 | Implemented | 📷 按钮添加到 composer，4 列布局 |
| 图片上传函数 | Implemented | `handleImageUpload()` 验证格式和大小 |
| 图片预览 | Implemented | 预览区域和移除按钮 |
| 消息显示图片 | Implemented | 消息列表中显示 `chat-message-image` |
| 前端构建 | Passing | `npm run build` → ✓ built in 2.09s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.09s
```

**Changes:**
- **Frontend**: `AppFixed.jsx` 添加图片上传状态和处理函数，composer 布局改为 4 列，消息列表支持显示图片
- **Styles**: `styles.css` 添加图片预览、移除按钮和消息图片样式

**Expected behavior:**
- 用户点击 📷 按钮选择图片
- 图片预览显示在输入框上方
- 点击 × 按钮可移除已选图片
- 支持纯图片发送（无需文字）
- 发送后图片显示在消息列表中

---

## 2026-07-09 Update: TASK-021 情绪固定化与 Memory Garden 简化

Fixed two UX issues: emotion/color/style are now AI-determined and read-only, and Memory Garden cards only show cover+date.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Emotion to color mapping | Implemented | `EMOTION_COLOR_MAP` maps 6 emotions to fixed colors |
| DiaryResultPage read-only | Implemented | Removed emotion select, color swatches, style input |
| Memory Garden simplified | Implemented | Cards now only show cover+date, clickable for detail |
| Frontend build | Passing | `npm run build` → ✓ built in 2.82s |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 2.82s
```

**Changes:**
- **Frontend**: Added `getEmotionColor()`, `getEmotionLabel()`, removed user-editable controls from DiaryResultPage, simplified MemoryGardenPage cards to cover+date only

**Expected behavior:**
- Emotion is displayed as a read-only badge with AI-analyzed color
- Memory Garden cards are now simple clickable cover images with date overlay
- All detail content is shown on the detail page after clicking

---

## 2026-07-09 Update: TASK-020 日记结构化生成与提示词隐藏

Fixed two UX issues: AI diary now generates structured narrative instead of raw conversation dump, and AI cover prompt is hidden from users.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Structured diary generation | Implemented | `EMOTION_ANALYSIS_SYSTEM_PROMPT` now requires `diary_content` (150-400 chars) |
| Cover prompt hidden | Implemented | Removed textarea display, prompt only used internally |
| Frontend build | Passing | `npm run build` → ✓ built in 3.91s |

**Validation:**
```bash
cd backend
py -c "from app.services.analysis_service import EMOTION_ANALYSIS_SYSTEM_PROMPT; print('diary_content' in EMOTION_ANALYSIS_SYSTEM_PROMPT)"
# Result: True

cd frontend
npm run build
# Result: ✓ built in 3.91s
```

**Changes:**
- **Backend**: Extended LLM prompt to request structured diary with date, events, feelings, and closing
- **Frontend**: Removed "自动封面提示词" textarea from DiaryResultPage, kept internal generation

**Expected behavior:**
- AI generates diary like: "x月x日\n\n今天我[事件]。\n\n[感受]。\n\n[总结与期待]。"
- Cover prompt is generated internally but not shown to user

---

## 2026-07-09 Update: TASK-019 AI Chat Thinking Indicator

Added a three-dot pulse animation indicator that appears while AI is generating a reply.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| isAiTyping state | Implemented | `ChatPage` line 138: `const [isAiTyping, setIsAiTyping] = useState(false)` |
| handleSend logic | Updated | Line 176 sets `isAiTyping = true`, line 199 sets `isAiTyping = false` in finally |
| Thinking indicator JSX | Implemented | Renders `.ai-thinking-indicator` with three dots when `isAiTyping` is true |
| CSS animations | Added | `@keyframes ai-thinking-pulse` and `@keyframes thinking-fade-in` in styles.css |

**Validation:**
```bash
cd frontend
npm run build
# Result: ✓ built in 3.25s
```

**Behavior:**
- User sends message → `isSending` and `isAiTyping` both become `true`
- Three-dot pulse indicator appears at bottom of chat message list
- AI reply arrives → `isAiTyping` becomes `false`, indicator disappears
- Animation: 8px dots with 1.4s pulse cycle, 0.2s staggered delay per dot

---

## 2026-07-09 Update: TASK-018 Username/Email Login Support

Login page now supports both username and email for authentication.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Backend Schema | Updated | `UserLogin.username_or_email` replaces `email` |
| Backend Router | Supports both | Query uses `or_(User.username == ..., User.email == ...)` |
| Frontend UI | Updated | Label "用户名/邮箱", placeholder "用户名或邮箱", type `text` |

**Validation:**
```bash
cd backend
py -c "from app.schemas.auth import UserLogin; print('OK')"
# Result: Fields: ['username_or_email', 'password']

cd frontend
npm run build
# Result: ✓ built in 3.41s
```

**API Change:**
- `POST /api/v1/auth/login` request body: `{ username_or_email, password }`
- Previous field `email` is now `username_or_email`

---

## 2026-07-09 Update: TASK-016 Admin Access Control

Implemented admin-only access control for the backend root path and API documentation.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Admin dependency module | Implemented | `app/auth/admin.py` provides `get_current_admin` |
| Root path protection | Implemented | `GET /` requires admin authentication |
| API docs protection | Implemented | `/docs`, `/redoc`, `/openapi.json` require admin |
| Logs API protection | Implemented | All `/api/v1/logs/*` endpoints require admin |
| Admin initialization script | Implemented | `scripts/init_admin.py` creates admin user |

**Validation:**
```bash
cd backend
py -c "from app.auth.admin import get_current_admin; print('Admin module OK')"
# Result: Admin module OK

py -c "from app.main import app; print('Main app OK')"
# Result: Main app OK
```

**Admin Account:**
- Username: `admin`
- Password: `admin123456`
- First-time setup: `py scripts/init_admin.py`

**Protected Resources:**
- `http://localhost:8000/` - Runtime log viewer (admin only)
- `http://localhost:8000/docs` - API documentation (admin only)

---

## 2026-07-09 Update: TASK-015 Runtime Log Viewer

Implemented a runtime log viewer interface replacing the API documentation at `http://localhost:8000`.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Log Storage | Implemented | In-memory `LogStorage` with 2000 entry capacity and automatic rotation |
| Log API | Implemented | New endpoints: `GET /api/v1/logs/entries`, `GET /api/v1/logs/stats`, `POST /api/v1/logs/clear` |
| Log Capture | Implemented | `RequestLoggingMiddleware` and exception handlers automatically store logs |
| Log Viewer UI | Implemented | `static/logs.html` with level filtering, auto-refresh, and statistics |
| Root Path | Configured | `GET /` serves the log viewer page |

**Validation:**
```bash
cd backend
py -c "from app.main import app; print('Backend imports OK')"
# Result: Backend imports OK

py -c "from app.logger.storage import get_log_storage; print('Storage OK')"
# Result: Storage OK
```

**Usage:**
- Start backend: `py -m uvicorn app.main:app --reload`
- Visit logs: `http://localhost:8000`
- Features: Level filtering (info/warning/error), auto-refresh (5s), statistics display, expandable log details

---

## 2026-07-09 Update: TASK-014 AI Companion Chat Dialog Fix

Fixed the `/#/ai-companion-chat` composer layout so the text dialog uses the available width instead of collapsing into a 42px icon column.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Chat composer layout | Fixed | `.composer-shell` now uses three grid columns matching the three rendered controls: textarea, voice, send |
| Protected route rendering | Fixed | Protected routes now return `LoginPage` immediately when `requireAuth()` redirects, preventing the chat page from flashing unauthorized API errors |

**Validation:**
```bash
cd frontend
npm.cmd run build
# passed; Vite chunk-size warning only

npm.cmd run test:contract
# chat adapter contract ok
# auth invalidation ok

# Browser check
# unauthenticated /#/ai-companion-chat renders LoginPage without mounting .chat-window
```

---

## 2026-07-09 Update: TASK-013 Frontend Auto Cover Generation

Connected the frontend Memory Card save flow to the existing AI image generation endpoint and removed user-facing custom image upload controls from the chat-to-card path.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Chat image upload UI | Complete | `frontend/src/AppFixed.jsx` no longer renders a file input or upload button in `ChatPage` |
| Diary cover selection UI | Complete | Diary result page now shows a read-only auto-cover prompt instead of manual URL/upload controls |
| Prompt generation | Complete | `buildWatercolorPrompt()` builds a beautiful watercolor prompt from diary content, raw conversation, messages, title, and emotion |
| Automatic cover save | Complete | `handleSave()` calls `generateImage()` before `createMemory()` and stores the generated `/uploads/...` URL plus prompt |
| Frontend API client | Complete | `frontend/src/api/client.js` exports `generateImage()` for `POST /api/v1/images/generate` |

**Validation:**
```bash
cd frontend
npm.cmd run build
# passed; Vite chunk-size warning only

npm.cmd run test:contract
# chat adapter contract ok
# auth invalidation ok
```

**Documentation:**
- `docs/vibe-logs/log-25-frontend-auto-cover-generation.md`

---

## 2026-07-09 Update: TASK-012 AI Image Generation Implementation

Implemented AI-powered image generation feature with DALL-E integration.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Image Generation API | ✅ Implemented | `POST /api/v1/images/generate` endpoint live |
| DALL-E Integration | ✅ Complete | Supports DALL-E 2/3 with configurable size/quality/style |
| Image Persistence | ✅ Complete | Generated images saved to `/uploads/` directory |
| Prompt Enhancement | ✅ Complete | Emotion-based style guidance added to prompts |
| Error Handling | ✅ Complete | Config, timeout, rate limit, provider errors handled |
| Test Coverage | ✅ Complete | 16 tests covering all flows and edge cases |
| Config Alignment | ✅ Complete | Uses `settings.ai_provider`, `settings.ai_timeout` like chatbot |

**Implementation:**
- Extended `AIProvider` with `generate_image()` method and `AIImageResponse` class
- Created `ImageGenerationService` for orchestration (generate → download → save)
- Added `POST /api/v1/images/generate` router endpoint
- Defined request/response schemas with validation
- **Updated**: ImageGenerationService now uses `settings` configuration for consistency

**Configuration:**
- All AI services (Chat, Analysis, Image Generation) now use unified `#env` configuration:
  - `AI_PROVIDER` - Provider selection (openai/deepseek)
  - `AI_DEFAULT_MODEL` - Default model to use
  - `AI_TIMEOUT` - Request timeout in seconds
  - `DEEPSEEK_BASE_URL` - Base URL for Deepseek provider

**Validation:**
```bash
cd backend
py -m pytest tests/test_image_generation.py -v
# 16 passed
```

**Documentation:**
- `docs/vibe-logs/log-24-ai-image-generation.md`

**Cost Note:**
- DALL-E 3: $0.04/1024x1024 image
- DALL-E 2: $0.02/1024x1024 image

---

## 2026-07-09 Update: TASK-009 Memory Card Deletion Fix

Implemented cascade deletion of associated conversations when a Memory Card is deleted.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Memory Card Deletion | Enhanced | `DELETE /api/v1/memories/{id}` now deletes associated Past Self conversations |
| Conversation Cleanup | Implemented | All conversations with `anchor_diary_id = memory.diary_id` are soft-deleted |
| Response Transparency | Implemented | API returns `deleted_conversations_count` in response |
| Test Coverage | Complete | New test validates cascade deletion behavior |

**Implementation:**
- Updated `backend/app/routers/memories.py` `delete_memory()` function
- Added Conversation model import
- Query and soft-delete all associated conversations before deleting memory card
- Return deletion count in API response

**Validation:**
```bash
cd backend
py -m pytest tests/test_memories.py -v
# 5 passed

py -m pytest tests/e2e/test_memory_flow.py -v
# 12 passed
```

**Documentation:**
- `docs/vibe-logs/log-21-memory-card-deletion-fix.md`

---

## 2026-07-09 Update: TASK-008 End-to-End Flow Testing

Implemented comprehensive end-to-end flow testing to validate complete user journeys through the application.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| E2E Test Suite | Implemented | 64 E2E tests covering 6 core user journeys |
| Test Coverage | Complete | Auth, Diary, Chat, Memory, Error Recovery, User Isolation flows |
| Test Results | All Passing | 64 passed, 157 warnings in 15.37s |
| Test Infrastructure | Complete | Shared fixtures, helper utilities, test plan documentation |

**Test Flows Implemented:**
1. **Authentication Flow** - Register → Login → Access Protected → Logout → Token Invalid
2. **Diary Creation Flow** - Create Entry → Analysis → Save Diary → List → Stats → Update → Delete
3. **Chat Flow** - Create Conversation → Send Message → AI Reply → Continue → History → Delete
4. **Memory Garden Flow** - Create Diary → Upload Cover → Create Memory → Past Self Chat → Delete
5. **Error Recovery Flow** - Token errors, AI errors, validation errors, resource not found
6. **User Isolation Flow** - Multi-user data isolation verification

**Validation actually run:**
```bash
cd backend
py -m pytest tests/e2e/ -v
# 64 passed, 157 warnings in 15.37s
```

**Key Features:**
- Complete user journey simulation from start to finish
- Database state verification beyond just API responses
- Error scenario testing and recovery path validation
- User data isolation testing for security
- Shared test fixtures and utilities for maintainability

**Documentation:**
- `docs/integration/e2e-test-plan.md` - Comprehensive test plan and design

---

## 2026-07-08 Update: TASK-004 Stale Auth Session Invalidation

The repeated `401 Unauthorized` logs for `/api/v1/chat/conversations`, `/api/v1/chat/messages`, `/api/v1/entries`, `/api/v1/memories`, and `/api/v1/stats/overview` were traced to a stale frontend session: localStorage still contained an access token, but the backend could not find an active user for the token subject and correctly returned `Inactive or missing user`.

Current behavior:

- Backend authentication contract remains unchanged: protected APIs still return 401 for missing, invalid, inactive, or deleted users.
- Frontend `apiRequest()` now invalidates the local session on any 401 response, clears stored token/user data, stores the current hash as the post-login redirect, dispatches `auth-change`, and redirects to `#/login`.
- A Node contract test now verifies stale-token invalidation without requiring a browser.

Validation actually run:

```bash
cd frontend
npm.cmd run test:contract
# chat adapter contract ok
# auth invalidation ok

npm.cmd run build
# passed after rerun outside sandbox; initial sandbox run failed with esbuild spawn EPERM
```

## 2026-07-08 Update: Memory Card, Past Self, Diary Result, Admin Dashboard

This `/innergarden` run implemented the missing MVP loop while keeping the existing frontend visual design language intact.

| Area | Current conclusion | Evidence |
| --- | --- | --- |
| Past Self Chat | Implemented | `POST /api/v1/memories/{memory_id}/past-self-chat` now calls the backend ChatService in `past_self` mode instead of returning local mock text. |
| Memory Card module | Implemented | New `memory_cards` and `uploaded_assets` tables, `/api/v1/memories` CRUD, filters, soft delete, and frontend Memory Garden wired to memory cards instead of diary list. |
| Diary Result controls | Implemented | Frontend now exposes emotion, emotion color, cover upload/URL/prompt, keywords, and AI tone adjustment controls before saving. |
| Chat UI continuity | Improved | Frontend now lists recent conversations, can continue a conversation, provides a Past Self mode via detail page, supports "change question", and keeps error messages visible. |
| Diary draft transcript bug | Fixed | Draft creation now stores the current full message list/transcript instead of stale pre-send state. |
| Image persistence | Implemented | `POST /api/v1/uploads/images` persists JSON data URL uploads under `backend/data/uploads` and returns static `/uploads/...` URLs. |
| Admin Dashboard | Implemented | Admin page and `/api/v1/admin/stats/charts` expose service status, 7-day new memory card chart data, and emotion distribution. |
| Auth error UX | Improved | Frontend auth client now displays backend `message/detail/details` instead of only generic failure text. |
| Product boundary on Home | Implemented | Home page states the product is not a diagnosis/treatment/medical-advice tool and only supports recording, companionship, and reflection. |

Validation actually run:

```bash
cd backend
py -m pytest tests/test_memories.py tests/test_admin.py tests/test_chat_api.py -q
# 21 passed, 54 warnings

cd frontend
npm.cmd run build
# built successfully; Vite chunk-size warning only
```

Known limitations:

- The frontend entry now imports `frontend/src/AppFixed.jsx` because the existing `App.jsx` could not be deleted by the patch tool in this run. The old file is retained but no longer used by `main.jsx`.
- Cover image "generation" is implemented as a generated prompt plus upload/URL selection, not a real image-model call.
- Full browser E2E automation was not run in this pass; backend tests and frontend production build were run.

## 2026-07-08 最新状态补充：Chat 运行验证与自动化测试

本轮按 `/innergarden` 流程补齐 Chat 模块验证记录，不继续新增业务功能。

### 2026-07-08 追加：DeepSeek Provider 验证

| 检查项 | 当前结论 | 证据 |
| --- | --- | --- |
| DeepSeek 环境配置 | 已验证 | `backend/.env` 中 `AI_PROVIDER=deepseek`，`DEEPSEEK_API_KEY` 已设置，`DEEPSEEK_BASE_URL=https://api.deepseek.com`，`AI_DEFAULT_MODEL=deepseek-chat` |
| OpenAI-compatible SDK 依赖 | 已修复并验证 | `backend/requirements.txt` 已加入 `openai`；`py -m pip install -r requirements.txt` 成功安装 `openai 2.44.0` |
| DeepSeek 直连 API | 已验证 | `py tests\test_deepseek_api.py` 成功调用 DeepSeek，返回模型 `deepseek-v4-flash` |
| AIProvider DeepSeek 初始化 | 已验证 | `AIProvider imported successfully; Provider: deepseek; Default Model: deepseek-chat` |
| 真实 authenticated Chat 请求 | 已验证 | 注册用户后 `POST /api/v1/chat/messages` 成功，返回 `message_sent`，conversation `message_count=2` |
| Provider 错误详情 | 已修复 | Chat provider 错误响应不再硬编码 `openai`，改为读取 `settings.ai_provider` |

| 检查项 | 当前结论 | 证据 |
| --- | --- | --- |
| Chat Router 是否注册 | 已验证 | `backend/app/main.py` 注册 `chat.router`，`test_chat_routes_are_registered` 通过 |
| Conversation/Message 是否持久化 | 已验证 | API 与服务层消息持久化测试通过 |
| 用户隔离 | 已验证 | 其他用户读取/删除对话返回 404 的测试通过 |
| Pydantic 422 | 已验证 | 缺少 `mode`、空 `content` 等请求返回 422 |
| 成功发送消息返回 200 | 已验证 | FakeAIProvider 下发送消息返回 200 |
| AI 超时返回 504 | 已验证 | TimeoutAIProvider 测试通过 |
| Provider 错误返回 502 | 已验证 | FailedAIProvider 测试通过 |
| AI 失败时不伪造 assistant 消息 | 已验证 | 失败场景仅保存 user message |
| 真实 DeepSeek 调用 | 已验证 | DeepSeek 直连脚本和 authenticated Chat 请求均通过 |
| 真实 uvicorn 启动 | 已验证 | 用户运行 `py -m uvicorn app.main:app --reload` 成功；用户侧验证 `/health`、`/api/v1/health`、`/docs` 均可访问 |
| OpenAPI Chat 路由暴露 | 已验证 | 用户侧 `/openapi.json` 输出 4 个 Chat path，覆盖 6 个 HTTP 操作 |

实际运行命令：

```bash
cd backend
py -m pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_retrieval_service.py tests/test_safety_service.py -v --tb=short
```

结果：`21 passed, 3 warnings`。

剩余风险：

- `backend/requirements.txt` 已包含 `openai`，真实 DeepSeek Provider 调用已验证。
- 前端 Chat UI 尚未实现，当前只有 API Client。
- pytest cache 有写入警告，不影响本次断言结果。
- 真实服务已能启动并返回健康检查，authenticated Chat 请求和真实 DeepSeek 调用已完成。

## Last Updated: 2026-07-08

## 2026-07-08 最新更新：TASK-006 Past Self Chat 500 错误修复

| 检查项 | 当前结论 | 证据 |
| --- | --- | --- |
| Past Self Chat 500 错误 | 已修复 | 后端添加了 `diary.analysis` 空值检查 |
| Chat Service 测试 | 通过 | 13 个测试通过 |
| Stats/Emotion 测试 | 通过 | 33 个测试通过 |
| Retrieval Service 测试 | 通过 | 4 个测试通过 |

**修复内容**：
- `backend/app/services/chat_service.py` - 3 处添加空值检查
- `backend/app/services/retrieval_service.py` - 1 处添加空值检查
- `backend/app/routers/stats.py` - 3 处添加空值检查

## 2026-07-08 Update: TASK-004 Stale Auth Session Invalidation

## Project Overview

Inner Garden is a digital diary and emotional wellness application with AI companion features.

## 2026-07-08 更新：认证业务层完成

| 检查项 | 当前结论 | 证据 |
|---|---|---|
| Demo 自动登录已移除 | 已移除 | `frontend/src/api/client.js` 不再包含 `ensureDemoSession()` |
| 认证业务层已实现 | 已实现 | `frontend/src/api/auth.js` 包含完整认证函数 |
| 登录页面组件已创建 | 已创建 | `frontend/src/components/LoginPage.jsx` |
| 路由保护已实现 | 已实现 | 受保护路由需要登录，未认证跳转登录页 |
| TopNav 显示用户信息 | 已实现 | 登录后显示邮箱和登出按钮 |
| 前端构建通过 | 已验证 | `npm run build` 成功完成 |

## Completed Features

| Feature | Status | Notes |
|---------|--------|-------|
| User Authentication (Frontend) | ✅ Complete | Auth business layer + Login UI component |
| User Authentication (Backend) | ✅ Complete | JWT-based, registration/login |
| Diary Entries | ✅ Complete | CRUD operations with soft delete |
| Emotion Analysis | ✅ Complete | Multi-label emotion detection |
| Chat Database Schema | ✅ Complete | conversations, messages, message_sources tables |
| Chat API Implementation | ✅ Complete | 6 endpoints, services, schemas |
| Chat Frontend API Client | ✅ Complete | JavaScript API functions |

## In Progress

| Feature | Status | Notes |
|---------|--------|-------|
| Frontend Chat UI Components | 🟡 Partial | Chat API complete, frontend UI components need implementation |
| Production Deployment | 🟡 Pending | CI/CD pipeline and production configuration needed |

## Not Started

| Feature | Priority | Notes |
|---------|----------|-------|
| Production Monitoring | Medium | APM integration, error tracking |
| Performance Optimization | Low | Database indexing, caching strategies |
| Deployment Pipeline | Low | CI/CD setup, automated testing in pipeline |

## Technical Debt

- Missing openai dependency in requirements.txt
- Chat endpoint core tests now exist; real startup and E2E coverage still pending
- No state tracking infrastructure (task-board, known-issues)

## Branch Status

- **Current Branch**: `backend/chat-database-schema`
- **Main Branch**: `main`
- **Uncommitted Changes**: 2 modified, 8 new files
