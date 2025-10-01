#!/bin/bash

# Unified startup script for Namaskah.App
echo "🚀 Starting Namaskah.App..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected"
    echo "💡 Run: source venv/bin/activate"
    
    # Try to activate automatically
    if [ -f "venv/bin/activate" ]; then
        echo "🔄 Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please create one:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# Start the unified Python starter
python3 start.py