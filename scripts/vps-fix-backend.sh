#!/bin/bash

################################################################################
# Inner Garden VPS Backend Fix Script
#
# Fixes missing aiohttp dependency by rebuilding backend container
#
# Usage: bash vps-fix-backend.sh
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/opt/inner-garden"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "=== Fixing VPS Backend: Rebuilding with aiohttp dependency ==="

cd "$PROJECT_DIR" || {
    log_error "Cannot access project directory: $PROJECT_DIR"
    exit 1
}

log_info "Stopping containers..."
docker compose -f docker-compose.prod.yml down

log_info "Rebuilding backend image (this may take a few minutes)..."
docker compose -f docker-compose.prod.yml build --no-cache backend

log_info "Starting containers..."
docker compose -f docker-compose.prod.yml up -d

log_info "Waiting for backend to be healthy..."
sleep 10

log_info "Checking container status..."
docker compose -f docker-compose.prod.yml ps

log_info "Testing backend health..."
curl -sS http://127.0.0.1:8000/health || {
    log_error "Backend health check failed"
    docker compose -f docker-compose.prod.yml logs --tail 20 backend
    exit 1
}

log_info "✅ Backend fix complete!"
log_info "Testing public API..."
curl -sS --max-time 10 http://jijiayi.online/api/v1/health

echo ""
log_info "✅ All services healthy!"
