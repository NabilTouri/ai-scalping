#!/bin/bash
# Deploy script for AI Scalping Bot
# Full install: curl -sSL https://raw.githubusercontent.com/NabilTouri/ai-scalping/main/deploy.sh | bash
# Quick update: ./deploy.sh update

set -e

APP_DIR="/opt/ai-scalping"

# Quick update mode
if [ "$1" == "update" ]; then
    echo "� Quick Update Mode"
    echo "===================="
    cd $APP_DIR
    git pull
    docker compose down
    docker compose up -d --build
    echo "✅ Update complete!"
    docker compose logs -f
    exit 0
fi

echo "�🚀 AI Scalping Bot - Deployment Script"
echo "======================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system..."
apt-get update -qq
apt-get upgrade -y -qq

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Create app directory
echo "📁 Setting up application in $APP_DIR..."
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update repo
if [ -d ".git" ]; then
    echo "🔄 Updating repository..."
    git pull
else
    echo "📥 Cloning repository..."
    git clone https://github.com/NabilTouri/ai-scalping.git .
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Please create /opt/ai-scalping/.env with your API keys:"
    echo ""
    echo "  ALPACA_API_KEY_CLAUDE=your_key"
    echo "  ALPACA_SECRET_KEY_CLAUDE=your_secret"
    echo "  ANTHROPIC_API_KEY=your_key"
    echo "  PAPER_TRADING=True"
    echo ""
    echo "Then run: cd /opt/ai-scalping && docker compose up -d"
    exit 0
fi

# Build and start
echo "🏗️  Building and starting bot..."
docker compose up -d --build

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Stop bot:      docker compose down"
echo "  Restart:       docker compose restart"
echo "  Quick update:  ./deploy.sh update"

