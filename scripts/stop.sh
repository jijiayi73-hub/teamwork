#!/bin/bash
# Inner Garden 停止脚本 (Linux/macOS)
# 优雅停止所有前后端服务

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo ""
echo -e "${YELLOW}🛑 Inner Garden 停止服务${NC}"
echo ""

STOPPED_COUNT=0

# 从 PID 文件读取并停止
if [ -f "$LOG_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
    if kill $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 后端已停止 (PID: $BACKEND_PID)${NC}"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  后端进程 $BACKEND_PID 未找到或已停止${NC}"
    fi
    rm -f "$LOG_DIR/backend.pid"
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
    if kill $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 前端已停止 (PID: $FRONTEND_PID)${NC}"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  前端进程 $FRONTEND_PID 未找到或已停止${NC}"
    fi
    rm -f "$LOG_DIR/frontend.pid"
fi

# 最后手段：按名称查找并停止
if [ $STOPPED_COUNT -eq 0 ]; then
    echo -e "${YELLOW}未找到 PID 文件，尝试按名称查找...${NC}"

    # 查找 uvicorn 进程
    UVICORN_PIDS=$(pgrep -f "uvicorn app.main:app" || true)
    if [ -n "$UVICORN_PIDS" ]; then
        echo "$UVICORN_PIDS" | while read pid; do
            if kill $pid 2>/dev/null; then
                echo -e "${GREEN}✅ 后端已停止 (PID: $pid)${NC}"
                STOPPED_COUNT=$((STOPPED_COUNT + 1))
            fi
        done
    fi

    # 查找 vite 进程
    VITE_PIDS=$(pgrep -f "vite.*--host" || true)
    if [ -n "$VITE_PIDS" ]; then
        echo "$VITE_PIDS" | while read pid; do
            if kill $pid 2>/dev/null; then
                echo -e "${GREEN}✅ 前端已停止 (PID: $pid)${NC}"
                STOPPED_COUNT=$((STOPPED_COUNT + 1))
            fi
        done
    fi
fi

echo ""
if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}👋 已停止 $STOPPED_COUNT 个服务${NC}"
else
    echo -e "${YELLOW}未找到运行中的服务${NC}"
fi
echo ""
