#!/bin/bash
# namaskah Deployment Script

set -e

echo "🚀 Starting namaskah deployment..."

# Check if running in production
if [ "$NODE_ENV" = "production" ] || [ "$ENVIRONMENT" = "production" ]; then
    echo "📦 Production deployment detected"
    ENV_FILE=".env.production"
else
    echo "🔧 Development deployment"
    ENV_FILE=".env"
fi

# Create environment file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating environment file from template..."
    if [ "$NODE_ENV" = "production" ]; then
        cp .env.production.example .env.production
        echo "⚠️  Please update .env.production with your production values"
    else
        cp .env.example .env
    fi
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations (if applicable)
if [ -f "alembic.ini" ]; then
    echo "🗄️  Running database migrations..."
    alembic upgrade head
fi

# Start the application
echo "🚀 Starting application..."
if [ "$NODE_ENV" = "production" ]; then
    # Production with Gunicorn
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
else
    # Development with auto-reload
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi