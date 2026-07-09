# Inner Garden VPS 部署指南

## 目标

将 Inner Garden 全套服务部署到 VPS (jijiayi.online)

## VPS 信息

- **域名**: jijiayi.online
- **IP**: 49.232.17.105
- **系统**: Ubuntu 22.04.5 LTS
- **用户**: ubuntu
- **SSH**: `vps` alias (配置在 `~/.ssh/config`)

## 当前状态

✅ SSH 连接正常
✅ Nginx 已安装 (1.18.0)
✅ Python 3.10.12 已安装
❌ Docker 未安装
❌ Docker Compose 未安装
❌ SSL 证书未配置

## 部署步骤

### 第 0 步: 准备本地项目

确保本地项目已构建完成：

```bash
# 前端构建
cd e:/Project/teamwork/frontend
npm run build

# 验证构建结果
ls -la dist/
```

### 第 1 步: 运行基础设施安装脚本

```bash
# 方式1: 直接在 VPS 上运行
scp scripts/vps-deploy.sh vps:~
ssh vps "bash ~/vps-deploy.sh"

# 方式2: 从本地通过管道运行
ssh vps 'bash -s' < scripts/vps-deploy.sh
```

这个脚本会：
- 安装 Docker 和 Docker Compose
- 创建项目目录 `/opt/inner-garden`
- 创建 `.env` 环境文件
- 创建 `docker-compose.yml`
- 配置 Nginx 反向代理
- 创建 systemd 服务

### 第 2 步: 复制项目文件到 VPS

```bash
# 创建 tar 包（只包含必要的文件）
cd e:/Project/teamwork
tar -czf inner-garden-deploy.tar.gz \
    backend/ \
    frontend/ \
    docker-compose.yml \
    .env.production \
    --exclude=node_modules \
    --exclude=__pycache__ \
    --exclude=.pytest_cache \
    --exclude=*.pyc \
    --exclude=dist \
    --exclude=.git

# 传输到 VPS
scp inner-garden-deploy.tar.gz vps:/opt/
```

### 第 3 步: 在 VPS 上解压并配置

```bash
ssh vps
cd /opt
tar -xzf inner-garden-deploy.tar.gz
mv teamwork inner-garden
cd inner-garden

# 配置环境变量
nano .env  # 更新 API keys
```

### 第 4 步: 构建 Docker 镜像

```bash
cd /opt/inner-garden
docker compose build
```

### 第 5 步: 启动服务

```bash
docker compose up -d
```

### 第 6 步: 配置 SSL 证书

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx -y

# 获取 SSL 证书
sudo certbot --nginx -d jijiayi.online -d www.jijiayi.online

# 测试自动续期
sudo certbot renew --dry-run
```

### 第 7 步: 运行数据库迁移

```bash
cd /opt/inner-garden
docker compose exec backend alembic upgrade head

# 创建管理员账户
docker compose exec backend python scripts/init_admin.py
```

### 第 8 步: 验证部署

```bash
# 检查容器状态
docker compose ps

# 检查日志
docker compose logs -f

# 测试健康检查
curl https://jijiayi.online/health
curl https://jijiayi.online/api/v1/health

# 访问网站
# https://jijiayi.online
```

## 环境变量配置

编辑 `/opt/inner-garden/.env`：

```bash
# AI Provider
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key  # 必填

# 或使用 OpenAI
# AI_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key

# SMTP (可选 - 用于密码重置)
SMTP_ENABLED=false  # 暂时禁用
```

## 常用命令

```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码
cd /opt/inner-garden
git pull
docker compose build
docker compose up -d

# 数据库备份
docker compose exec backend sqlite3 data/app.db ".backup data/app.db.backup"

# 进入容器
docker compose exec backend bash
docker compose exec frontend sh
```

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker compose logs backend

# 检查端口占用
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8080
```

### Nginx 502 错误

```bash
# 检查 upstream 配置
sudo nginx -t

# 检查容器是否在运行
docker compose ps

# 重启 nginx
sudo systemctl restart nginx
```

### SSL 证书问题

```bash
# 查看证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew

# 查看 nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

## 安全建议

1. **防火墙配置**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **定期备份**:
   ```bash
   # 创建备份脚本
   cat > ~/backup-inner-garden.sh <<'EOF'
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cd /opt/inner-garden
   docker compose exec backend sqlite3 data/app.db ".backup data/app.db.backup.$DATE"
   tar -czf ~/backups/inner-garden-$DATE.tar.gz data/
   EOF
   ```

3. **日志轮转**: 配置 logrotate 管理日志文件大小

## 监控

建议安装监控工具：
- Prometheus + Grafana
- Uptime Kuma
- 或简单的健康检查脚本

## 回滚

如果部署出现问题：

```bash
# 停止服务
docker compose down

# 恢复备份
cd /opt
mv inner-garden inner-garden.failed
mv inner-garden.backup.YYYYMMDD_HHMMSS inner-garden

# 重启服务
cd inner-garden
docker compose up -d
```
