#!/usr/bin/env python3
"""
namaskah Setup Script
Helps configure the project for development and production
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {text}")
    print("=" * 60)


def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 40)


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def create_env_file():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from .env.example")
            print("📝 Please edit .env file with your API keys")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")


def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True


def create_directories():
    """Create necessary directories"""
    directories = ["static", "logs", "models", "data"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_git_hooks():
    """Setup git hooks if git is available"""
    if os.path.exists(".git"):
        try:
            # Create a simple pre-commit hook
            hook_content = """#!/bin/sh
# Simple pre-commit hook for namaskah
echo "Running pre-commit checks..."

# Check for Python syntax errors
python -m py_compile main.py textverified_client.py groq_client.py mock_twilio_client.py

if [ $? -ne 0 ]; then
    echo "❌ Python syntax errors found. Commit aborted."
    exit 1
fi

echo "✅ Pre-commit checks passed"
"""

            hook_path = ".git/hooks/pre-commit"
            with open(hook_path, "w") as f:
                f.write(hook_content)

            os.chmod(hook_path, 0o755)
            print("✅ Git pre-commit hook installed")
        except Exception as e:
            print(f"⚠️  Could not setup git hooks: {e}")
    else:
        print("⚠️  Not a git repository, skipping git hooks")


def check_api_keys():
    """Check if API keys are configured"""
    print("\n🔑 API Key Configuration Status:")

    # Load .env file
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value

    # Check each service
    services = {
        "TextVerified": ["TEXTVERIFIED_API_KEY", "TEXTVERIFIED_EMAIL"],
        "Twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        "Groq AI": ["GROQ_API_KEY"],
    }

    for service, keys in services.items():
        configured = all(
            env_vars.get(key, "").replace("your_", "") != "" for key in keys
        )
        status = "✅ Configured" if configured else "❌ Not configured"
        print(f"   {service}: {status}")

        if not configured:
            print(
                f"     Missing: {', '.join([k for k in keys if not env_vars.get(k, '').replace('your_', '')])}"
            )


def create_startup_scripts():
    """Create convenient startup scripts"""

    # Development startup script
    dev_script = """#!/bin/bash
# namaskah Development Startup Script

echo "🚀 Starting namaskah in development mode..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
echo "🌟 Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

    with open("start_dev.sh", "w") as f:
        f.write(dev_script)
    os.chmod("start_dev.sh", 0o755)

    # Production startup script
    prod_script = """#!/bin/bash
# namaskah Production Startup Script

echo "🚀 Starting namaskah in production mode..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start with gunicorn for production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
"""

    with open("start_prod.sh", "w") as f:
        f.write(prod_script)
    os.chmod("start_prod.sh", 0o755)

    print("✅ Created startup scripts: start_dev.sh, start_prod.sh")


def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")

    try:
        # Test imports
        import fastapi
        import requests
        import uvicorn

        print("✅ Core dependencies importable")

        # Test custom modules
        from clients.groq_client import GroqAIClient
        from clients.mock_twilio_client import MockTwilioClient
        from clients.textverified_client import TextVerifiedClient

        print("✅ Custom modules importable")

        # Test mock Twilio client
        mock_client = MockTwilioClient()
        message = mock_client.messages.create(
            body="Test message", from_="+1555000001", to="+1234567890"
        )
        print(f"✅ Mock Twilio client working (Message SID: {message.sid})")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

    return True


def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete! Next Steps:")

    steps = [
        "Edit .env file with your API keys (TextVerified, Groq)",
        "Run the development server: ./start_dev.sh or uvicorn main:app --reload",
        "Open http://localhost:8000 to see the dashboard",
        "Run the demo: python demo_platform.py",
        "Check the API documentation at http://localhost:8000/docs",
    ]

    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")

    print("\n📚 Additional Resources:")
    print("   - TextVerified API: https://www.textverified.com/")
    print("   - Groq AI: https://console.groq.com/")
    print("   - FastAPI Docs: https://fastapi.tiangolo.com/")

    print("\n🎯 Mock Mode:")
    print("   The platform runs in mock mode by default (USE_MOCK_TWILIO=true)")
    print("   This allows full testing without real Twilio credentials")


def main():
    """Main setup function"""
    print_header("namaskah Platform Setup")

    print_step(1, "Checking Python version")
    check_python_version()

    print_step(2, "Creating environment file")
    create_env_file()

    print_step(3, "Installing dependencies")
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return

    print_step(4, "Creating directories")
    create_directories()

    print_step(5, "Setting up git hooks")
    setup_git_hooks()

    print_step(6, "Creating startup scripts")
    create_startup_scripts()

    print_step(7, "Checking API configuration")
    check_api_keys()

    print_step(8, "Running tests")
    if not run_tests():
        print("⚠️  Some tests failed, but setup can continue")

    print_next_steps()


if __name__ == "__main__":
    main()
