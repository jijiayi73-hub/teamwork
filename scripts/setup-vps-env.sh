#!/bin/bash
# Setup production .env file on VPS

cd /opt/inner-garden

# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)

# Create production .env
cat > .env <<EOF
# 应用环境
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# 数据库
DATABASE_URL=sqlite:///./data/app.db

# 安全
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=https://jijiayi.online,https://www.jijiayi.online

# AI Provider
AI_PROVIDER=deepseek
AI_DEFAULT_MODEL=deepseek-chat
AI_TIMEOUT=30
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 火山引擎 (可选)
VOLCES_API_KEY=${VOLCES_API_KEY}
VOLCES_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCES_IMAGE_MODEL=doubao-seedream-5-0-260128

# SMTP (暂时禁用)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_FROM=Inner Garden <noreply@jijiayi.online>
SMTP_USE_TLS=true
SMTP_ENABLED=false
EOF

echo "✅ .env 文件已创建"
echo "SECRET_KEY=${SECRET_KEY}"
echo ""
echo "⚠️  请设置以下环境变量:"
echo "   - DEEPSEEK_API_KEY (必需)"
echo "   - VOLCES_API_KEY (可选)"
echo "   - SMTP_USER 和 SMTP_PASSWORD (可选)"
