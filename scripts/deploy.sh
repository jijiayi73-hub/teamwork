#!/bin/bash

################################################################################
# Inner Garden Deployment Script for Ubuntu
# This script deploys the application to an Ubuntu server using Docker Compose
#
# Usage: ./deploy.sh [environment]
#   environment: development, staging, production (default: production)
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
ENVIRONMENT="${1:-production}"
PROJECT_NAME="inner-garden"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
GIT_REPO="${GIT_REPO:-https://github.com/your-org/inner-garden.git}"
GIT_BRANCH="${GIT_BRANCH:-main}"
BACKUP_DIR="/opt/${PROJECT_NAME}-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

check_requirements() {
    log_info "Checking requirements..."

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_warning "This script should be run with sudo privileges"
        log_info "Re-running with sudo..."
        exec sudo "$0" "$@"
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        install_docker
    else
        log_success "Docker is installed"
    fi

    # Check if Docker Compose is installed
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        install_docker_compose
    else
        log_success "Docker Compose is installed"
    fi

    # Check if Git is installed
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Installing..."
        apt-get update && apt-get install -y git
    fi
}

install_docker() {
    log_info "Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    log_success "Docker installed successfully"
}

install_docker_compose() {
    log_info "Docker Compose is included in Docker Compose Plugin"
    log_info "Using 'docker compose' command instead of 'docker-compose'"
}

backup_current() {
    if [ -d "$DEPLOY_DIR" ]; then
        log_info "Creating backup of current deployment..."
        mkdir -p "$BACKUP_DIR"

        # Stop containers before backup
        cd "$DEPLOY_DIR"
        docker compose stop || true

        # Create backup
        BACKUP_PATH="$BACKUP_DIR/backup_${TIMESTAMP}"
        cp -r "$DEPLOY_DIR" "$BACKUP_PATH"

        # Keep only last 5 backups
        ls -t "$BACKUP_DIR"/ | tail -n +6 | xargs -I {} rm -rf "$BACKUP_DIR/{}"

        log_success "Backup created at $BACKUP_PATH"
    else
        log_info "No existing deployment to backup"
    fi
}

clone_or_update_repo() {
    log_info "Setting up project files..."

    if [ -d "$DEPLOY_DIR/.git" ]; then
        log_info "Updating existing repository..."
        cd "$DEPLOY_DIR"
        git fetch origin
        git reset --hard "origin/${GIT_BRANCH}"
        git pull origin "${GIT_BRANCH}"
    else
        log_info "Cloning repository..."
        mkdir -p "$DEPLOY_DIR"
        git clone -b "${GIT_BRANCH}" "$GIT_REPO" "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
    fi

    log_success "Repository updated"
}

setup_environment() {
    log_info "Setting up environment..."

    # Copy environment file if it doesn't exist
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        if [ -f "$DEPLOY_DIR/.env.example" ]; then
            cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
            log_warning ".env file created from .env.example"
            log_warning "Please edit $DEPLOY_DIR/.env with your production values"
        else
            log_warning "No .env.example found, creating basic .env"
            cat > "$DEPLOY_DIR/.env" << EOF
# Environment
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=sqlite:///./data/app.db

# Security
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://your-domain.com

# AI Provider
AI_PROVIDER=deepseek
AI_DEFAULT_MODEL=deepseek-chat
AI_TIMEOUT=30
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=your-openai-api-key

# Ports
HTTP_PORT=80
HTTPS_PORT=443
EOF
        fi
    fi

    # Create necessary directories
    mkdir -p "$DEPLOY_DIR/nginx/ssl"
    mkdir -p "$DEPLOY_DIR/data/uploads"
    mkdir -p "$DEPLOY_DIR/logs"

    # Set proper permissions
    chmod -R 755 "$DEPLOY_DIR"

    log_success "Environment setup complete"
}

build_and_deploy() {
    log_info "Building and deploying containers..."

    cd "$DEPLOY_DIR"

    # Build images
    log_info "Building Docker images (this may take a while)..."
    docker compose build --no-cache

    # Stop old containers
    log_info "Stopping old containers..."
    docker compose down

    # Start new containers
    log_info "Starting new containers..."
    docker compose up -d

    # Wait for health check
    log_info "Waiting for services to be healthy..."
    sleep 15

    # Check service health
    if docker compose ps | grep -q "healthy\|running"; then
        log_success "Services started successfully"
    else
        log_error "Some services may not be healthy"
        docker compose ps
    fi
}

setup_ssl() {
    log_info "Setting up SSL (if certificates provided)..."

    # Check if SSL certificates exist
    if [ -f "$DEPLOY_DIR/nginx/ssl/cert.pem" ] && [ -f "$DEPLOY_DIR/nginx/ssl/key.pem" ]; then
        log_success "SSL certificates found"
        # Update nginx.conf to enable HTTPS
        # This would be automated in a more sophisticated script
    else
        log_warning "No SSL certificates found. HTTP only."
        log_info "To enable HTTPS, place certificates at:"
        log_info "  - $DEPLOY_DIR/nginx/ssl/cert.pem"
        log_info "  - $DEPLOY_DIR/nginx/ssl/key.pem"
    fi
}

create_systemd_service() {
    log_info "Creating systemd service for auto-start..."

    cat > "/etc/systemd/system/${PROJECT_NAME}.service" << EOF
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

    systemctl daemon-reload
    systemctl enable "${PROJECT_NAME}.service"

    log_success "Systemd service created and enabled"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    docker image prune -af
    log_success "Cleanup complete"
}

print_deployment_info() {
    log_success "=========================================="
    log_success "Deployment completed successfully!"
    log_success "=========================================="
    echo ""
    log_info "Deployment directory: $DEPLOY_DIR"
    log_info "Environment: $ENVIRONMENT"
    echo ""
    log_info "Service URLs:"
    log_info "  - HTTP: http://$(hostname -f | || echo 'your-domain.com')"
    log_info "  - Health: http://$(hostname -f || echo 'your-domain.com')/health"
    echo ""
    log_info "Useful commands:"
    log_info "  - View logs: docker compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
    log_info "  - Restart: docker compose -f $DEPLOY_DIR/docker-compose.yml restart"
    log_info "  - Stop: systemctl stop $PROJECT_NAME"
    log_info "  - Start: systemctl start $PROJECT_NAME"
    echo ""
    log_warning "Remember to:"
    log_warning "  1. Edit $DEPLOY_DIR/.env with your production values"
    log_warning "  2. Add SSL certificates for HTTPS"
    log_warning "  3. Configure firewall (ufw) to allow ports 80 and 443"
    echo ""
}

# Main deployment flow
main() {
    log_success "Starting Inner Garden deployment..."
    log_info "Environment: $ENVIRONMENT"
    echo ""

    check_requirements
    backup_current
    clone_or_update_repo
    setup_environment
    build_and_deploy
    setup_ssl
    create_systemd_service
    cleanup_old_images
    print_deployment_info
}

# Run main function
main "$@"
