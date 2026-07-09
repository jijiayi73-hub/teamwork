#!/bin/bash

################################################################################
# Inner Garden Update Script for Ubuntu
# This script updates the application with zero-downtime deployment
#
# Usage: ./update.sh [branch]
#   branch: Git branch to update from (default: main)
################################################################################

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GIT_BRANCH="${1:-main}"
PROJECT_NAME="inner-garden"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
BACKUP_DIR="/opt/${PROJECT_NAME}-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=5

# Functions
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

check_deployment_exists() {
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deployment not found at $DEPLOY_DIR"
        log_info "Please run deploy.sh first"
        exit 1
    fi
}

create_backup() {
    log_info "Creating backup..."

    mkdir -p "$BACKUP_DIR"

    # Backup database
    cd "$DEPLOY_DIR"
    if [ -f "data/app.db" ]; then
        cp "data/app.db" "$BACKUP_DIR/app.db.${TIMESTAMP}"
        log_success "Database backed up"
    fi

    # Backup .env file
    if [ -f ".env" ]; then
        cp ".env" "$BACKUP_DIR/.env.${TIMESTAMP}"
        log_success "Environment file backed up"
    fi

    # Keep only last N backups
    ls -t "$BACKUP_DIR"/app.db.* 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
    ls -t "$BACKUP_DIR"/.env.* 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm

    log_success "Backup completed"
}

update_code() {
    log_info "Updating codebase..."

    cd "$DEPLOY_DIR"

    # Stash any local changes (just in case)
    git stash

    # Fetch and pull latest
    git fetch origin "${GIT_BRANCH}"
    git reset --hard "origin/${GIT_BRANCH}"

    log_success "Code updated to latest ${GIT_BRANCH}"
}

rollback() {
    log_error "Update failed! Rolling back..."

    cd "$DEPLOY_DIR"

    # Restore database
    if [ -f "$BACKUP_DIR/app.db.${TIMESTAMP}" ]; then
        cp "$BACKUP_DIR/app.db.${TIMESTAMP}" "data/app.db"
        log_info "Database restored"
    fi

    # Restore .env
    if [ -f "$BACKUP_DIR/.env.${TIMESTAMP}" ]; then
        cp "$BACKUP_DIR/.env.${TIMESTAMP}" ".env"
        log_info "Environment file restored"
    fi

    # Reset git to previous state
    git reset --hard HEAD@{1}

    # Restart with old code
    docker compose down
    docker compose up -d

    log_success "Rollback completed"
    exit 1
}

rebuild_services() {
    log_info "Rebuilding services..."

    cd "$DEPLOY_DIR"

    # Build new images
    if ! docker compose build --no-cache; then
        log_error "Build failed"
        rollback
    fi

    # Recreate containers (zero-downtime for nginx)
    log_info "Recreating containers..."
    docker compose up -d --no-deps --build backend frontend
    docker compose up -d nginx

    log_success "Services rebuilt"
}

wait_for_healthy() {
    log_info "Waiting for services to be healthy..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost/health > /dev/null 2>&1; then
            log_success "Services are healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "Services failed health check"
    rollback
}

cleanup() {
    log_info "Cleaning up..."

    cd "$DEPLOY_DIR"

    # Remove old images
    docker image prune -f

    # Remove dangling volumes
    docker volume prune -f

    log_success "Cleanup completed"
}

run_migrations_if_needed() {
    log_info "Checking for database migrations..."

    cd "$DEPLOY_DIR"

    # Run migrations in backend container
    if docker compose exec -T backend alembic upgrade head 2>/dev/null; then
        log_success "Database migrations completed"
    else
        log_warning "Migration check failed or not needed"
    fi
}

print_update_info() {
    log_success "=========================================="
    log_success "Update completed successfully!"
    log_success "=========================================="
    echo ""
    log_info "Current branch: $GIT_BRANCH"
    log_info "Deployment directory: $DEPLOY_DIR"
    echo ""
    log_info "Recent backups:"
    ls -t "$BACKUP_DIR"/app.db.* 2>/dev/null | head -3 || echo "  No backups found"
    echo ""
    log_info "To rollback if needed:"
    log_info "  1. Copy backup: cp $BACKUP_DIR/app.db.<timestamp> $DEPLOY_DIR/data/app.db"
    log_info "  2. Reset git: cd $DEPLOY_DIR && git reset --hard HEAD@{1}"
    log_info "  3. Rebuild: docker compose up -d --build"
    echo ""
}

# Main update flow
main() {
    log_success "Starting Inner Garden update..."
    log_info "Branch: $GIT_BRANCH"
    echo ""

    check_deployment_exists
    create_backup
    update_code
    rebuild_services
    wait_for_healthy
    run_migrations_if_needed
    cleanup
    print_update_info
}

# Run main function
main "$@"
