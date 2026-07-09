#!/bin/bash

################################################################################
# Inner Garden 自动部署脚本 (本地 → VPS)
#
# 此脚本在本地运行，自动化整个部署流程：
# 1. 本地前端构建
# 2. 传输文件到VPS
# 3. VPS上重新构建容器
# 4. 运行数据库迁移
# 5. 验证部署健康状态
#
# Usage:
#   bash scripts/auto-deploy.sh [mode]
#
# Modes:
#   quick   - 仅重启容器（代码更改，无依赖更改）
#   full    - 完整部署（重新构建容器）
#   migrate - 仅运行数据库迁移
#
# Default: full
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VPS_HOST="vps"
VPS_DEPLOY_DIR="/opt/inner-garden"
DOMAIN="jijiayi.online"
MODE="${1:-full}"

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
# Step 1: 本地准备
################################################################################
local_prepare() {
    log_info "=== Step 1: 本地准备 ==="

    cd "$PROJECT_ROOT"

    # 检查 git 状态
    log_info "检查 Git 状态..."
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "工作目录有未提交的更改："
        git status --short
        read -p "继续部署？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "部署已取消"
            exit 1
        fi
    else
        log_success "工作目录干净"
    fi

    # 构建前端
    log_info "构建前端..."
    cd "$PROJECT_ROOT/frontend"
    npm run build

    if [ $? -eq 0 ]; then
        log_success "前端构建成功"
    else
        log_error "前端构建失败"
        exit 1
    fi

    cd "$PROJECT_ROOT"
}

################################################################################
# Step 2: 传输文件到VPS
################################################################################
transfer_files() {
    log_info "=== Step 2: 传输文件到VPS ==="

    log_info "使用 rsync 传输文件..."

    rsync -avz --delete \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.pyc' \
        --exclude='dist' \
        --exclude='.pytest_cache' \
        --exclude='build' \
        --exclude='.eggs' \
        --exclude='*.egg-info' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='.env.local' \
        --exclude='.DS_Store' \
        "$PROJECT_ROOT/" "$VPS_HOST:$VPS_DEPLOY_DIR/"

    if [ $? -eq 0 ]; then
        log_success "文件传输成功"
    else
        log_error "文件传输失败"
        exit 1
    fi
}

################################################################################
# Step 3: VPS上部署
################################################################################
vps_deploy() {
    log_info "=== Step 3: VPS上部署 ==="

    if [ "$MODE" = "quick" ]; then
        log_info "模式: 快速部署（仅重启容器）"
        ssh "$VPS_HOST" "cd $VPS_DEPLOY_DIR && docker compose restart backend frontend"
    elif [ "$MODE" = "full" ]; then
        log_info "模式: 完整部署（重新构建容器）"
        ssh "$VPS_HOST" "
            cd $VPS_DEPLOY_DIR
            docker compose build
            docker compose up -d
        "
    elif [ "$MODE" = "migrate" ]; then
        log_info "模式: 仅运行数据库迁移"
    else
        log_error "未知模式: $MODE"
        exit 1
    fi

    if [ $? -eq 0 ]; then
        log_success "容器部署成功"
    else
        log_error "容器部署失败"
        exit 1
    fi
}

################################################################################
# Step 4: 运行数据库迁移
################################################################################
run_migrations() {
    log_info "=== Step 4: 运行数据库迁移 ==="

    ssh "$VPS_HOST" "
        cd $VPS_DEPLOY_DIR
        echo '等待 backend 容器就绪...'
        sleep 5
        echo '当前迁移版本:'
        docker compose exec -T backend alembic current || echo '无法获取当前版本'
        echo '运行迁移:'
        docker compose exec -T backend alembic upgrade head
    "

    if [ $? -eq 0 ]; then
        log_success "数据库迁移成功"
    else
        log_warning "数据库迁移失败或跳过（可能没有新迁移）"
    fi
}

################################################################################
# Step 5: 验证部署
################################################################################
verify_deployment() {
    log_info "=== Step 5: 验证部署 ==="

    # 检查容器状态
    log_info "检查容器状态..."
    ssh "$VPS_HOST" "cd $VPS_DEPLOY_DIR && docker compose ps"

    # 检查健康状态
    log_info "检查健康状态..."
    sleep 3

    HEALTH_CHECK=$(curl -fsS "https://$DOMAIN/api/v1/health" || echo "failed")

    if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
        log_success "健康检查通过"
        echo "$HEALTH_CHECK" | jq . || echo "$HEALTH_CHECK"
    else
        log_warning "健康检查失败"
        echo "响应: $HEALTH_CHECK"
    fi
}

################################################################################
# Main Execution
################################################################################
main() {
    log_success "=========================================="
    log_success "Inner Garden 自动部署"
    log_success "模式: $MODE"
    log_success "=========================================="
    echo ""

    # Check if ssh connection works
    log_info "检查 SSH 连接..."
    if ! ssh "$VPS_HOST" "echo 'SSH 连接成功'" > /dev/null 2>&1; then
        log_error "无法连接到 VPS，请检查 SSH 配置"
        exit 1
    fi

    # Run deployment steps
    case "$MODE" in
        quick)
            # quick mode: skip local build and transfer files
            log_warning "快速模式：跳过本地构建和文件传输"
            vps_deploy
            verify_deployment
            ;;
        migrate)
            # migrate mode: only run migrations
            log_warning "迁移模式：仅运行数据库迁移"
            run_migrations
            ;;
        full)
            # full deployment
            local_prepare
            transfer_files
            vps_deploy
            run_migrations
            verify_deployment
            ;;
        *)
            log_error "未知模式: $MODE"
            echo "支持的模式: quick, full, migrate"
            exit 1
            ;;
    esac

    echo ""
    log_success "=========================================="
    log_success "部署完成！"
    log_success "=========================================="
    echo ""
    log_info "查看日志:"
    log_info "  ssh $VPS_HOST \"cd $VPS_DEPLOY_DIR && docker compose logs -f\""
    echo ""
    log_info "访问网站:"
    log_info "  https://$DOMAIN"
}

# Run main function
main "$@"
