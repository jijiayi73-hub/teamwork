# Inner Garden VPS 部署状态

## 2026-07-09 最新更新：TASK-031 滚动修复部署 ✅

已部署 TASK-031 (聊天对话框滚动修复) 到生产环境。

| 项目 | 状态 | 说明 |
|------|------|------|
| 前端容器 | ✅ | 重新构建并重启，包含滚动修复 |
| 后端容器 | ✅ | 正常运行 |
| 健康检查 | ✅ | `https://jijiayi.online/api/v1/health` 返回 healthy |
| 前端页面 | ✅ | `https://jijiayi.online/` 返回有效 HTML |

**部署内容**：
- 移除 `.ai-notification-list` 的 `justify-content: flex-end`
- 添加 `messagesEndRef` 和自动滚动 `useEffect`
- 新消息到达时自动滚动到底部
- 用户可以自由向上滚动查看历史消息

**验证**：
```bash
ssh vps "docker ps --filter 'name=inner-garden'"
# inner-garden-frontend   Up (healthy)
# inner-garden-backend    Up (healthy)

curl https://jijiayi.online/api/v1/health
# {"success":true,"data":{"status":"healthy"},"message":"ok"}
```

---

## 2026-07-09 最新状态：已部署 ✅

Inner Garden 已部署到 VPS `/opt/inner-garden`，前端和后端容器均为 healthy，公网 HTTPS 访问已验证，SSL 证书已配置。

| 项目 | 状态 | 说明 |
|------|------|------|
| Docker 镜像源 | ✅ | 腾讯云镜像优先，DaoCloud 备用 |
| 后端镜像 | ✅ | `inner-garden-backend:latest` 构建成功 |
| 前端镜像 | ✅ | `inner-garden-frontend:latest` 构建成功 |
| 后端容器 | ✅ | `inner-garden-backend` healthy |
| 前端容器 | ✅ | `inner-garden-frontend` healthy |
| 数据库迁移 | ✅ | `alembic upgrade head` 已执行 |
| Nginx | ✅ | 配置语法通过，代理到 `127.0.0.1:8000` / `127.0.0.1:8080` |
| 公网前端 | ✅ | `https://jijiayi.online/` 返回 200 |
| 公网 API | ✅ | `https://jijiayi.online/api/v1/health` 返回 healthy |
| SSL | ✅ | Let's Encrypt 证书已配置，有效期至 2026-10-07 |
| AI Key | ⚠️ | `/opt/inner-garden/.env` 仍为 `DEEPSEEK_API_KEY=YOUR_KEY` |

### 本轮修复

- 修复 Docker registry 超时：`/etc/docker/daemon.json` 改为腾讯云镜像优先、DaoCloud 备用。
- 修复后端镜像 OOM：`backend/Dockerfile` 移除未使用的 `gcc` / `libpq-dev` 安装层。
- 修复后端启动失败：`analysis_service.py` 运行时导入 `sqlalchemy.orm.Session`。
- 修复前端 healthcheck 误判：使用 `127.0.0.1:8080/health`，避免 `localhost` 解析到 IPv6 后连接失败。

### 已执行验证

```bash
ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml ps"
# inner-garden-backend healthy
# inner-garden-frontend healthy

ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"
# SQLite migration context completed without error

ssh vps "curl -fsS http://127.0.0.1:8000/health"
# {"success":true,"data":{"status":"healthy"},"message":"ok","request_id":"local"}

ssh vps "curl -sS --max-time 10 https://jijiayi.online/api/v1/health"
# {"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}

curl -sS https://jijiayi.online/api/v1/health
# {"success":true,"data":{"status":"healthy","api_version":"v1"},"message":"ok","request_id":"local"}
```

### 后续待办

1. **（必需）** 在 `/opt/inner-garden/.env` 配置真实 `DEEPSEEK_API_KEY`，然后重启后端：
   ```bash
   ssh vps "nano /opt/inner-garden/.env"
   # 修改 DEEPSEEK_API_KEY=YOUR_KEY 为真实密钥
   ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml restart backend"
   ```

**已完成 2026-07-09：SSL 证书配置**
- ✅ Let's Encrypt 证书已成功配置
- ✅ HTTPS 访问已验证：`https://jijiayi.online`
- ✅ 证书有效期：2026-10-07
- ✅ 自动续期任务已配置

> 以下旧版“待完成”清单已被本节取代，保留作为部署过程记录。

## 已完成 ✅

| 步骤 | 状态 | 说明 |
|------|------|------|
| SSH 连接测试 | ✅ | VPS 连接正常 |
| Docker 安装 | ✅ | Docker 29.6.1 + Compose v5.3.1 |
| 项目目录创建 | ✅ | /opt/inner-garden |
| 文件复制 | ✅ | backend/frontend/docker-compose 已复制 |
| .env 配置 | ✅ | SECRET_KEY 已生成 |
| docker-compose.yml | ✅ | 生产配置已准备 |

## 待完成 ⏳

由于权限限制，以下步骤需要手动执行：

### 1. 配置 Docker 镜像加速（必需）

```bash
ssh vps
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

或运行：`ssh vps 'bash -s' < scripts/configure-docker-mirror.sh`

### 2. 构建 Docker 镜像

```bash
ssh vps
cd /opt/inner-garden
docker compose -f docker-compose.prod.yml build
```

### 3. 启动服务

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. 配置 Nginx

```bash
sudo cp /tmp/inner-garden-nginx.conf /etc/nginx/sites-available/inner-garden.conf
sudo ln -sf /etc/nginx/sites-available/inner-garden.conf /etc/nginx/sites-enabled/inner-garden.conf
sudo rm -f /etc/nginx/sites-enabled/jijiayi.online.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 5. 配置 API Keys

```bash
ssh vps
cd /opt/inner-garden
nano .env  # 设置 DEEPSEEK_API_KEY
```

### 6. 运行数据库迁移

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend python scripts/init_admin.py
```

### 7. 配置 SSL 证书（可选）

```bash
sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot --nginx -d jijiayi.online -d www.jijiayi.online
```

## 快速执行

复制以下命令一次性执行：

```bash
# 配置 Docker 镜像并构建
ssh vps '
sudo mkdir -p /etc/docker
echo "{\"registry-mirrors\": [\"https://docker.m.daocloud.io\"]}" | sudo tee /etc/docker/daemon.json
sudo systemctl daemon-reload && sudo systemctl restart docker
cd /opt/inner-garden
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
'

# 配置 Nginx
ssh vps '
sudo cp /tmp/inner-garden-nginx.conf /etc/nginx/sites-available/inner-garden.conf
sudo ln -sf /etc/nginx/sites-available/inner-garden.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/jijiayi.online.conf
sudo nginx -t && sudo systemctl reload nginx
'
```

## 验证部署

```bash
# 检查容器状态
ssh vps 'docker ps'

# 检查服务健康
curl http://jijiayi.online/health
curl http://jijiayi.online/api/v1/health
```

## 关键信息

| 项目 | 值 |
|------|------|
| 域名 | jijiayi.online |
| 项目目录 | /opt/inner-garden |
| 后端端口 | 8000 |
| 前端端口 | 8080 |
| SECRET_KEY | 9eb7cb13a7252b2a88d83efb45e3a6843722f030091f8bcad9b697c409f0775d |
