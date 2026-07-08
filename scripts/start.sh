#!/bin/bash
# Inner Garden 一键启动脚本 (Linux/macOS)
# 首次运行自动安装依赖，后续快速启动

set -e

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
FLAG_FILE="$BACKEND_DIR/.installed"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "🌱 Inner Garden 启动中..."
echo ""

# 创建日志目录
mkdir -p "$LOG_DIR"

# ============================================================================
# 1. 快速路径：已安装则直接启动
# ============================================================================
if [ -f "$FLAG_FILE" ] && [ -d "$BACKEND_DIR/venv" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${GREEN}✅ 依赖已就绪，快速启动${NC}"
    goto start_services 2>/dev/null || true
fi

# ============================================================================
# 2. 首次安装路径
# ============================================================================
echo -e "${YELLOW}🔧 首次运行，设置环境...${NC}"

# 检测 Python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 未找到 Python，请先安装"
        exit 1
    fi
fi

# 检测 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到 npm，请先安装 Node.js"
    exit 1
fi

echo -e "  📦 安装后端依赖..."
cd "$BACKEND_DIR"
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# 检查 .env
if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
    echo -e "  ⚙️ 创建 .env 配置..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo -e "  ${YELLOW}⚠️ 请配置 .env 中的 API 密钥${NC}"
fi

echo -e "  📦 安装前端依赖..."
cd "$FRONTEND_DIR"
npm install --silent --no-audit --no-fund

# 标记安装完成
touch "$FLAG_FILE"
echo -e "  ${GREEN}✅ 安装完成！${NC}"
echo ""

# ============================================================================
# 3. 启动服务
# ============================================================================
start_services() {
    echo -e "${BLUE}🚀 启动服务...${NC}"
    echo ""

    # 启动后端
    cd "$BACKEND_DIR"
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"

    # 启动前端
    cd "$FRONTEND_DIR"
    npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"

    sleep 2

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 Inner Garden 已启动!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "  📡 后端 API:   ${BLUE}http://localhost:8000${NC}"
    echo "  📄 API 文档:   ${BLUE}http://localhost:8000/docs${NC}"
    echo "  🌐 前端界面:   ${BLUE}http://localhost:5173${NC}"
    echo ""
    echo "  按 Ctrl+C 停止所有服务"
    echo ""

    # 优雅停止
    cleanup() {
        echo ""
        echo "🛑 正在停止服务..."
        [ -f "$LOG_DIR/backend.pid" ] && kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null && rm -f "$LOG_DIR/backend.pid"
        [ -f "$LOG_DIR/frontend.pid" ] && kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null && rm -f "$LOG_DIR/frontend.pid"
        echo -e "${GREEN}✅ 已停止${NC}"
        exit 0
    }
    trap cleanup SIGINT SIGTERM
    wait
}

start_services
