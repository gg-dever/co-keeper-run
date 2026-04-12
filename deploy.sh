#!/bin/bash
# Quick deployment script for CoKeeper

set -e

echo "🚀 CoKeeper Production Deployment"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from template..."
    cp .env.production .env
    echo ""
    echo "📝 Please edit .env with your actual values:"
    echo "   - Your domain name"
    echo "   - QuickBooks production credentials"
    echo "   - Xero production credentials"
    echo ""
    echo "Run this script again after configuring .env"
    exit 1
fi

# Check if SSL certificates exist
if [ ! -d ssl ] || [ ! -f ssl/fullchain.pem ]; then
    echo "⚠️  SSL certificates not found in ./ssl/"
    echo ""
    echo "Please run these commands first:"
    echo "  sudo certbot certonly --standalone -d your-domain.com"
    echo "  mkdir -p ssl"
    echo "  sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/"
    echo "  sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/"
    echo "  sudo chmod 644 ssl/*.pem"
    exit 1
fi

echo "✅ Configuration files found"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app should be available at: https://$(grep DOMAIN .env | cut -d '=' -f2)"
echo ""
echo "📝 View logs with:"
echo "   docker-compose logs -f"
echo ""
echo "🔍 Test health endpoint:"
echo "   curl https://$(grep DOMAIN .env | cut -d '=' -f2)/health"
