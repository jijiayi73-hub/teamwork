# Log-44: Memory Garden 情绪花园筛选功能修复

## 任务信息

**日期**: 2026-07-10  
**相关任务**: TASK-039  
**类型**: Debug / Frontend + Backend integration  
**状态**: Fixed locally, deployment pending at time of writing

## 目标

修复情绪花园筛选功能，让用户可以可靠地按情绪和关键词筛选记忆卡片。

## Existing Context

Memory Garden 使用 `frontend/src/AppFixed.jsx` 中的 `MemoryGardenPage` 渲染，数据来自 `GET /api/v1/memories`。已有 API 查询参数为 `emotion` 和 `keyword`。

## Progress Truth Audit Summary

| Claim | Evidence read | Verdict |
| --- | --- | --- |
| Memory Garden 使用 `AppFixed.jsx` | `frontend/src/main.jsx` 历史状态记录；本轮 `rg` 定位到 `MemoryGardenPage` | verified |
| 后端已支持 `emotion` 和 `keyword` 参数 | `backend/app/routers/memories.py` | verified |
| 关键词筛选体验不完整 | 源码显示后端只匹配 `keywords_json`，前端情绪选择只更新 state 不立即加载 | verified |
| 本次未改变 API 字段或状态码 | `memories.py`, `client.js`, `test_memories.py` diff | verified |

## Key Prompts

用户请求：`debug 情绪花园的筛选功能 并将改动对齐到vps`

## AI Proposed Plan

1. 先按 Inner Garden Evidence Gate 读取状态、任务板、已知问题和相关源码。
2. 定位筛选前端交互和后端 API 行为。
3. 做最小修复并增加回归测试。
4. 跑后端测试、前端契约测试和生产构建。
5. 更新状态文档，再同步到 VPS。

## 修改内容

| 文件 | 修改 |
| --- | --- |
| `frontend/src/AppFixed.jsx` | 情绪下拉变化后立即加载；关键词输入框支持 Enter；增加清除筛选按钮 |
| `frontend/src/api/client.js` | 使用 `import.meta.env?.VITE_API_BASE_URL`，让 Node 契约测试可导入 API client |
| `frontend/nginx.conf` | HTML shell 返回 `no-store, no-cache`，hash assets 保持 immutable，降低旧 HTML 指向旧资源导致黑屏的风险 |
| `backend/app/routers/memories.py` | `keyword` 匹配扩展到关键词、标题、正文、会话摘要、封面提示和情绪标签 |
| `backend/tests/test_memories.py` | 新增标题关键词、摘要关键词与情绪组合筛选回归测试 |

## Human Checks And Validation

```bash
cd backend
py -m pytest tests/test_memories.py -q
# 6 passed, 19 warnings

cd frontend
npm.cmd run test:contract
# chat adapter contract ok
# auth invalidation ok

cd frontend
npm.cmd run build
# initial sandbox runs failed with esbuild spawn EPERM
# rerun outside sandbox passed, built in 4.31s

ssh vps "curl -I -sS https://jijiayi.online/"
# Cache-Control: no-store, no-cache, must-revalidate, max-age=0

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml ps"
# backend healthy, frontend healthy
```

## Problems Encountered

- 后端测试首次导入失败，因为当前 Python 环境缺少项目已声明的 `aiohttp` 依赖；通过 `py -m pip install aiohttp` 补齐。
- 普通 pip 安装受系统 Temp 权限影响，改用工作区临时目录并提权安装。
- 前端 `npm.cmd run test:contract` 暴露 `import.meta.env` 在 Node 中为空的问题，已修复。
- `npm.cmd run build` 在 sandbox 内遇到 Vite/esbuild `spawn EPERM`，提权重跑后通过。
- VPS 浏览器黑屏反馈后，发现生产 HTML 没有显式 no-cache 头。由于 Vite 静态资源使用 hash 文件名且 assets 是 immutable，旧 HTML 可能引用已经不存在的旧 hash 资源。已修复前端 Nginx 缓存策略。

## Iterations

第一轮定位到前端只改 state、不主动加载，以及后端只查 `keywords_json`。第二轮增加测试后发现环境依赖和 Node 契约测试兼容性问题，并一并修复。

## Final Result

本地筛选修复已完成。API 查询参数保持不变，用户可继续使用 `emotion` 和 `keyword` 筛选。关键词现在更贴近用户可见卡片文本，不再局限于手动关键词数组。

VPS 前后端容器已重新构建并启动；HTML shell 现在强制不缓存，降低部署后浏览器继续使用旧 shell 导致黑屏的风险。

## Team Understanding And Reflection

筛选功能属于前后端共同体验：前端必须明确触发加载，后端关键词范围也要符合用户对“按关键词搜索卡片”的直觉。以后改这类列表功能时，应同时检查 UI 触发、API 参数和测试覆盖。

## Related Files

- `frontend/src/AppFixed.jsx`
- `frontend/src/api/client.js`
- `frontend/nginx.conf`
- `backend/app/routers/memories.py`
- `backend/tests/test_memories.py`
- `docs/state/current-status.md`
- `docs/state/task-board.md`

## Related Commit Or PR

Pending.
