#!/bin/bash
# Simple Docker deployment script

echo "🐳 Namaskah.App - Simple Docker Deployment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Create data directory for persistence
mkdir -p data

echo "🔄 Building Docker image..."
docker build -f Dockerfile.simple -t namaskah-app:simple .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

echo "🚀 Starting application..."
docker-compose -f docker-compose.simple.yml up -d

if [ $? -eq 0 ]; then
    echo "✅ Application started successfully"
    echo ""
    echo "🔗 Access your app at:"
    echo "   • App: http://localhost:8000"
    echo "   • API Docs: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo ""
    echo "📊 Useful commands:"
    echo "   • View logs: docker-compose -f docker-compose.simple.yml logs -f"
    echo "   • Stop app: docker-compose -f docker-compose.simple.yml down"
    echo "   • Restart: docker-compose -f docker-compose.simple.yml restart"
else
    echo "❌ Failed to start application"
    exit 1
fi