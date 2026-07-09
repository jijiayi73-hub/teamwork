#!/bin/bash

################################################################################
# Inner Garden VPS Deployment Script for jijiayi.online
#
# This script automates the full deployment of Inner Garden to the VPS
#
# Usage:
#   1. Copy this script to the VPS: scp vps-deploy.sh vps:~
#   2. Run on VPS: ssh vps "bash ~/vps-deploy.sh"
#   3. Or run from local: ssh vps 'bash -s' < vps-deploy.sh
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
# Step 1: Install Docker
################################################################################
install_docker() {
    log_info "=== Step 1: Installing Docker ==="

    if command -v docker &> /dev/null; then
        log_success "Docker already installed: $(docker --version)"
        return
    fi

    log_info "Updating package index..."
    sudo apt-get update -qq

    log_info "Installing required packages..."
    sudo apt-get install -y ca-certificates curl gnupg lsb-release

    log_info "Adding Docker's official GPG key..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    log_info "Setting up Docker repository..."
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    log_info "Installing Docker Engine..."
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    log_info "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker

    log_success "Docker installed: $(docker --version)"
    log_success "Docker Compose: $(docker compose version)"
}

################################################################################
# Step 2: Create Project Directory
################################################################################
setup_project_dir() {
    log_info "=== Step 2: Setting up project directory ==="

    if [ -d "$DEPLOY_DIR" ]; then
        log_warning "Project directory exists, creating backup..."
        sudo mv "$DEPLOY_DIR" "${DEPLOY_DIR}.backup.${TIMESTAMP}"
    fi

    sudo mkdir -p "$DEPLOY_DIR"
    sudo mkdir -p "$DEPLOY_DIR/nginx"
    sudo mkdir -p "$DEPLOY_DIR/data/uploads"
    sudo mkdir -p "$DEPLOY_DIR/logs"

    log_success "Project directory created: $DEPLOY_DIR"
}

################################################################################
# Step 3: Create Production .env File
################################################################################
create_env_file() {
    log_info "=== Step 3: Creating production environment file ==="

    # Generate secure secret key
    SECRET_KEY=$(openssl rand -hex 32)

    sudo tee "$DEPLOY_DIR/.env" > /dev/null <<EOF
# Environment
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# Database (SQLite for simplicity, can be upgraded to PostgreSQL)
DATABASE_URL=sqlite:///./data/app.db

# Security
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

# AI Provider
AI_PROVIDER=deepseek
AI_DEFAULT_MODEL=deepseek-chat
AI_TIMEOUT=30
DEEPSEEK_API_KEY=\${DEEPSEEK_API_KEY}
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=\${OPENAI_API_KEY}

# Ports
HTTP_PORT=80
HTTPS_PORT=443

# Frontend API URL (will be proxied through nginx)
VITE_API_BASE_URL=/api

# SMTP (optional - for password reset)
SMTP_HOST=\${SMTP_HOST:-smtp.gmail.com}
SMTP_PORT=587
SMTP_USER=\${SMTP_USER}
SMTP_PASSWORD=\${SMTP_PASSWORD}
SMTP_FROM=Inner Garden <noreply@${DOMAIN}>
SMTP_USE_TLS=true
SMTP_ENABLED=false
EOF

    log_success "Environment file created"
    log_warning "Please update API keys in $DEPLOY_DIR/.env"
}

################################################################################
# Step 4: Create docker-compose.yml
################################################################################
create_docker_compose() {
    log_info "=== Step 4: Creating docker-compose.yml ==="

    sudo tee "$DEPLOY_DIR/docker-compose.yml" > /dev/null <<'EOF'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: inner-garden-backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - APP_ENV=production
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
    volumes:
      - ./backend:/app
      - backend-data:/app/data
      - backend-logs:/app/logs
    networks:
      - inner-garden-network
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    expose:
      - "8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=/api
    container_name: inner-garden-frontend
    restart: unless-stopped
    networks:
      - inner-garden-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    expose:
      - "8080"

networks:
  inner-garden-network:
    driver: bridge

volumes:
  backend-data:
    driver: local
  backend-logs:
    driver: local
EOF

    log_success "docker-compose.yml created"
}

################################################################################
# Step 5: Create nginx Configuration
################################################################################
create_nginx_config() {
    log_info "=== Step 5: Creating nginx configuration ==="

    sudo tee /etc/nginx/sites-available/${PROJECT_NAME}.conf > /dev/null <<EOF
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

    # SSL Configuration (will be added after certbot)
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    # ssl_protocols TLSv1.2 TLSv1.3;
    # ssl_prefer_server_ciphers on;

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

    # Remove old config symlink if exists
    sudo rm -f /etc/nginx/sites-enabled/${DOMAIN}.conf
    sudo rm -f /etc/nginx/sites-enabled/00-edge-http.conf

    # Create new symlink
    sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME}.conf /etc/nginx/sites-enabled/${PROJECT_NAME}.conf

    log_success "Nginx configuration created"
}

################################################################################
# Step 6: Set Permissions
################################################################################
set_permissions() {
    log_info "=== Step 6: Setting permissions ==="

    sudo chown -R \$USER:\$USER "$DEPLOY_DIR"
    sudo chmod -R 755 "$DEPLOY_DIR"

    log_success "Permissions set"
}

################################################################################
# Step 7: Create systemd service
################################################################################
create_systemd_service() {
    log_info "=== Step 7: Creating systemd service ==="

    sudo tee /etc/systemd/system/${PROJECT_NAME}.service > /dev/null <<EOF
[Unit]
Description=Inner Garden Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${DEPLOY_DIR}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${PROJECT_NAME}.service

    log_success "Systemd service created"
}

################################################################################
# Main Execution
################################################################################
main() {
    log_success "=========================================="
    log_success "Inner Garden VPS Deployment"
    log_success "Domain: ${DOMAIN}"
    log_success "=========================================="
    echo ""

    install_docker
    setup_project_dir
    create_env_file
    create_docker_compose
    create_nginx_config
    set_permissions
    create_systemd_service

    echo ""
    log_success "=========================================="
    log_success "Infrastructure setup complete!"
    log_success "=========================================="
    echo ""
    log_info "Next steps:"
    log_info "  1. Copy project files to: $DEPLOY_DIR"
    log_info "  2. Update API keys in: $DEPLOY_DIR/.env"
    log_info "  3. Build containers: cd $DEPLOY_DIR && docker compose build"
    log_info "  4. Start services: docker compose up -d"
    log_info "  5. Setup SSL: sudo certbot --nginx -d ${DOMAIN}"
    log_info "  6. Run migrations: docker compose exec backend alembic upgrade head"
    echo ""
    log_warning "IMPORTANT: Update DEEPSEEK_API_KEY in .env before starting!"
}

# Run main function
main "$@"
