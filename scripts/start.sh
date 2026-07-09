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
BACKEND_VENV_DIR="$BACKEND_DIR/.venv"

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

check_python_version() {
    "$1" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}

find_python() {
    for candidate in python3.11 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && check_python_version "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

wait_for_url() {
    local url="$1"
    local name="$2"
    local attempts=20

    for _ in $(seq 1 "$attempts"); do
        if python - "$url" <<'PY' >/dev/null 2>&1
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as response:
    raise SystemExit(0 if 200 <= response.status < 500 else 1)
PY
        then
            echo -e "  ${GREEN}✅ $name 已就绪${NC}"
            return 0
        fi
        sleep 1
    done

    echo "❌ $name 启动失败，请查看 logs 目录"
    return 1
}

cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    [ -f "$LOG_DIR/backend.pid" ] && kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null && rm -f "$LOG_DIR/backend.pid"
    [ -f "$LOG_DIR/frontend.pid" ] && kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null && rm -f "$LOG_DIR/frontend.pid"
    echo -e "${GREEN}✅ 已停止${NC}"
}

# ============================================================================
# 1. 检测运行环境
# ============================================================================

# 检测 Python
if ! PYTHON_CMD="$(find_python)"; then
    echo "❌ 未找到 Python 3.11+，请先安装 Python 3.11 或更高版本"
    exit 1
fi

# 检测 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到 npm，请先安装 Node.js"
    exit 1
fi

# ============================================================================
# 2. 安装依赖
# ============================================================================

if [ -f "$FLAG_FILE" ] && [ -d "$BACKEND_VENV_DIR" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${GREEN}✅ 依赖已就绪，快速启动${NC}"
else
    echo -e "${YELLOW}🔧 首次运行，设置环境...${NC}"

    echo -e "  📦 安装后端依赖..."
    cd "$BACKEND_DIR"
    "$PYTHON_CMD" -m venv "$BACKEND_VENV_DIR"
    source "$BACKEND_VENV_DIR/bin/activate"
    python -m pip install -q -r requirements.txt

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
fi

# ============================================================================
# 3. 启动服务
# ============================================================================
echo -e "${BLUE}🚀 启动服务...${NC}"
echo ""

# 准备数据库
cd "$BACKEND_DIR"
source "$BACKEND_VENV_DIR/bin/activate"
python -m alembic upgrade head

# 启动后端
uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"

# 启动前端
cd "$FRONTEND_DIR"
npm run dev -- --host 127.0.0.1 > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"

if ! wait_for_url "http://127.0.0.1:8000/api/v1/health" "后端 API"; then
    tail -n 40 "$LOG_DIR/backend.log" || true
    cleanup
    exit 1
fi

if ! wait_for_url "http://127.0.0.1:5173" "前端界面"; then
    tail -n 40 "$LOG_DIR/frontend.log" || true
    cleanup
    exit 1
fi

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
trap 'cleanup; exit 0' SIGINT SIGTERM
wait
