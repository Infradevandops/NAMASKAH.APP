#!/bin/bash

# 🚀 Frontend Build Script for namaskah
# This script builds the React frontend for production

set -e  # Exit on any error

echo "🚀 Building namaskah Frontend..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: Frontend directory not found"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend directory"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Build the React app
echo "🔨 Building React app for production..."
npm run build

# Check if build was successful
if [ -d "build" ]; then
    echo "✅ Frontend build completed successfully!"
    echo "📁 Build files are in: frontend/build/"
    echo "🌐 You can now start the FastAPI server to serve the React app"
    echo ""
    echo "Next steps:"
    echo "  1. cd .. (back to project root)"
    echo "  2. uvicorn main:app --host 0.0.0.0 --port 8000"
    echo "  3. Open http://localhost:8000"
else
    echo "❌ Build failed - build directory not created"
    exit 1
fi