#!/bin/bash

################################################################################
# Inner Garden 一键部署脚本
#
# 方式 A: 一键执行（推荐）
#
# 此脚本整合完整的部署流程：
# 1. 配置 Docker 镜像加速
# 2. 构建 + 启动容器
# 3. 配置 Nginx
# 4. 设置 API Key
# 5. 运行数据库迁移
# 6. 创建管理员账户
#
# Usage:
#   ssh vps 'bash -s' < scripts/one-click-deploy.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="inner-garden"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
DOMAIN="jijiayi.online"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# Step 1: 配置 Docker 镜像加速
################################################################################
configure_docker_mirror() {
    log_info "=== Step 1: 配置 Docker 镜像加速 ==="

    sudo mkdir -p /etc/docker

    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

    # 重启 Docker
    sudo systemctl daemon-reload
    sudo systemctl restart docker

    log_success "Docker 镜像加速配置完成"
    docker info | grep -A 5 'Registry Mirrors' || log_warning "未检测到镜像源配置"
}

################################################################################
# Step 2: 构建 + 启动容器
################################################################################
build_and_start() {
    log_info "=== Step 2: 构建 + 启动容器 ==="

    cd "$DEPLOY_DIR"

    log_info "停止现有容器（如果有）..."
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true

    log_info "构建 Docker 镜像（无缓存）..."
    docker compose -f docker-compose.prod.yml build --no-cache

    log_info "启动容器..."
    docker compose -f docker-compose.prod.yml up -d

    log_success "容器启动完成"
    docker compose -f docker-compose.prod.yml ps
}

################################################################################
# Step 3: 配置 Nginx
################################################################################
configure_nginx() {
    log_info "=== Step 3: 配置 Nginx ==="

    # 创建 Nginx 配置
    sudo tee /tmp/${PROJECT_NAME}-nginx.conf > /dev/null <<EOF
# Inner Garden Upstream
upstream inner_garden_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream inner_garden_frontend {
    server 127.0.0.1:8080;
    keepalive 32;
}

# HTTP Server - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    # Allow Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all HTTP traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client upload size
    client_max_body_size 10M;

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Backend API
    location /api/ {
        proxy_pass http://inner_garden_backend;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static uploads
    location /uploads/ {
        proxy_pass http://inner_garden_backend/uploads/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;

        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend SPA
    location / {
        proxy_pass http://inner_garden_frontend;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        return 503 "Service temporarily unavailable";
    }
}
EOF

    # 复制配置文件
    sudo cp /tmp/${PROJECT_NAME}-nginx.conf /etc/nginx/sites-available/${PROJECT_NAME}.conf
    sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME}.conf /etc/nginx/sites-enabled/${PROJECT_NAME}.conf

    # 移除旧配置
    sudo rm -f /etc/nginx/sites-enabled/${DOMAIN}.conf 2>/dev/null || true
    sudo rm -f /etc/nginx/sites-enabled/00-edge-http.conf 2>/dev/null || true

    # 测试并重载 Nginx
    sudo nginx -t && sudo systemctl reload nginx

    log_success "Nginx 配置完成"
}

################################################################################
# Step 4: 设置 API Key
################################################################################
set_api_key() {
    log_info "=== Step 4: 设置 API Key ==="

    cd "$DEPLOY_DIR"

    log_warning "⚠️  请手动设置 DEEPSEEK_API_KEY："
    log_warning "   ssh vps \"cd /opt/inner-garden && nano .env\""
    log_warning "   找到 DEEPSEEK_API_KEY= 行，填入你的密钥"
    log_warning "   然后按 Ctrl+X, Y, Enter 保存"
}

################################################################################
# Step 5: 运行数据库迁移
################################################################################
run_migrations() {
    log_info "=== Step 5: 运行数据库迁移 ==="

    cd "$DEPLOY_DIR"

    log_info "等待 backend 容器就绪..."
    sleep 5

    log_info "运行 Alembic 迁移..."
    docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

    log_success "数据库迁移完成"
}

################################################################################
# Step 6: 创建管理员账户
################################################################################
create_admin() {
    log_info "=== Step 6: 创建管理员账户 ==="

    cd "$DEPLOY_DIR"

    log_info "运行 init_admin.py 脚本..."
    docker compose -f docker-compose.prod.yml exec backend python scripts/init_admin.py || {
        log_warning "管理员账户可能已存在或脚本未找到"
    }

    log_success "管理员账户创建完成"
}

################################################################################
# Main Execution
################################################################################
main() {
    log_success "=========================================="
    log_success "Inner Garden 一键部署"
    log_success "Domain: ${DOMAIN}"
    log_success "=========================================="
    echo ""

    configure_docker_mirror
    build_and_start
    configure_nginx
    set_api_key
    run_migrations
    create_admin

    echo ""
    log_success "=========================================="
    log_success "部署完成！"
    log_success "=========================================="
    echo ""
    log_info "验证部署："
    log_info "  curl https://${DOMAIN}/health"
    log_info "  curl https://${DOMAIN}/api/v1/health"
    echo ""
    log_warning "别忘了设置 DEEPSEEK_API_KEY！"
}

# Run main function
main "$@"
