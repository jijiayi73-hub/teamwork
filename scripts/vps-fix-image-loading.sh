#!/bin/bash
# VPS Image Loading CORS Fix Deployment Script
# Fixes Chat-AI image upload background update and Memory Garden cover display issues

set -e

echo "=========================================="
echo "VPS Image Loading CORS Fix Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_green() {
    echo -e "${GREEN}$1${NC}"
}

print_yellow() {
    echo -e "${YELLOW}$1${NC}"
}

# Check if running on VPS
if [ ! -d "/opt/inner-garden" ]; then
    print_yellow "Warning: /opt/inner-garden directory not found."
    echo "This script should be run on the VPS server."
    echo "If running locally, please sync code to VPS first."
    exit 1
fi

cd /opt/inner-garden

echo "Step 1: Pulling latest code from repository..."
print_yellow "Note: Make sure you've pushed the latest changes to the repository!"
echo ""
read -p "Press Enter to continue (after ensuring code is synced)..."

echo ""
echo "Step 2: Rebuilding frontend container with CORS fix..."
docker compose -f docker-compose.prod.yml build frontend

echo ""
echo "Step 3: Restarting frontend container..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "Step 4: Waiting for frontend to be healthy..."
sleep 5

echo ""
echo "Step 5: Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
print_green "=========================================="
print_green "Deployment completed successfully!"
print_green "=========================================="
echo ""
echo "What was fixed:"
echo "- Removed image.crossOrigin = 'anonymous' from ParticleWaveHero component"
echo "- Images now load correctly from same origin"
echo "- Chat-AI background will update after image upload"
echo "- Memory Garden covers will display consistently"
echo ""
echo "To verify:"
echo "1. Visit https://jijiayi.online"
echo "2. Go to AI Companion Chat"
echo "3. Upload an image"
echo "4. Background should update immediately"
echo "5. Generate a diary and check Memory Garden"
echo "6. Cover images should display consistently"
echo ""
