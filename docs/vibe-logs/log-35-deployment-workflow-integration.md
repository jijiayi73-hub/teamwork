# 部署工作流集成到 innergarden skill

**日期**: 2026-07-09
**任务**: 将 VPS 部署流程集成到 `/innergarden` skill 中
**状态**: ✅ 完成

---

## 目标

将本地到 VPS 的部署流程封装进 innergarden skill，让用户可以通过简单的命令完成部署。

---

## 实现内容

### 1. 新增部署工作流模块

**文件**: `.claude/skills/innergarden/modules/deployment-workflow.md`

提供完整的部署流程指南，包括：
- VPS 配置信息（域名、IP、部署目录）
- 部署模式（quick/full/migration/rollback/verification）
- 本地准备步骤（前端构建、本地测试）
- 三种部署方法（rsync/tar/git）
- VPS 部署命令
- 验证和回滚程序
- 快速参考命令表

### 2. 更新 innergarden skill

**文件**: `.claude/skills/innergarden/SKILL.md`

- 添加 `deploy` 操作模式
- 在内部模块列表中添加 `deployment-workflow.md`
- 在路由规则中添加部署相关路由

### 3. 创建自动部署脚本

**文件**: `scripts/auto-deploy.sh`

提供一键部署功能，支持三种模式：
- `full` - 完整部署（本地构建 → 传输文件 → 重建容器 → 运行迁移 → 验证）
- `quick` - 快速部署（仅重启容器）
- `migrate` - 仅运行数据库迁移

---

## 使用方式

### 通过 innergarden skill

```bash
/innergarden 部署到生产环境
/innergarden 更新 VPS 上的代码
/innergarden 运行数据库迁移
```

### 通过自动部署脚本

```bash
# 完整部署（推荐用于有依赖更改的更新）
bash scripts/auto-deploy.sh full

# 快速部署（仅代码更改，无依赖更改）
bash scripts/auto-deploy.sh quick

# 仅运行迁移
bash scripts/auto-deploy.sh migrate
```

### 手动部署（参考部署模块）

```bash
# 1. 本地构建
cd frontend && npm run build

# 2. 传输文件
rsync -avz --exclude='node_modules' \
    --exclude='__pycache__' --exclude='.git' \
    e:/Project/teamwork/ vps:/opt/inner-garden/

# 3. VPS 部署
ssh vps "cd /opt/inner-garden && docker compose build && docker compose up -d"

# 4. 运行迁移
ssh vps "cd /opt/inner-garden && docker compose exec backend alembic upgrade head"

# 5. 验证
curl https://jijiayi.online/api/v1/health
```

---

## 快速参考命令

| 操作 | 命令 |
|------|------|
| 查看日志 | `ssh vps "cd /opt/inner-garden && docker compose logs -f"` |
| 重启服务 | `ssh vps "cd /opt/inner-garden && docker compose restart"` |
| 停止服务 | `ssh vps "cd /opt/inner-garden && docker compose down"` |
| 进入容器 | `ssh vps "cd /opt/inner-garden && docker compose exec backend bash"` |
| 运行迁移 | `ssh vps "cd /opt/inner-garden && docker compose exec backend alembic upgrade head"` |
| 检查迁移 | `ssh vps "cd /opt/inner-garden && docker compose exec backend alembic current"` |
| 容器状态 | `ssh vps "cd /opt/inner-garden && docker compose ps"` |

---

## 验证

部署完成后，通过以下命令验证：

```bash
# 容器状态
ssh vps "cd /opt/inner-garden && docker compose ps"

# 健康检查
curl https://jijiayi.online/api/v1/health
```

预期输出：
```json
{"success":true,"data":{"status":"healthy"},"message":"ok","request_id":"local"}
```

---

## VPS 配置信息

| 项目 | 值 |
|------|------|
| 域名 | jijiayi.online |
| IP | 49.232.17.105 |
| 系统 | Ubuntu 22.04.5 LTS |
| 用户 | ubuntu |
| SSH | `vps` alias |
| 部署目录 | /opt/inner-garden |

---

## 相关文件

- `.claude/skills/innergarden/modules/deployment-workflow.md` - 部署工作流模块
- `scripts/auto-deploy.sh` - 自动部署脚本
- `scripts/vps-deploy.sh` - VPS 初始部署脚本
- `scripts/one-click-deploy.sh` - 一键部署脚本（在VPS上运行）
- `docs/vps-deployment-guide.md` - VPS 部署指南
- `docs/vps-deployment-status.md` - VPS 部署状态
