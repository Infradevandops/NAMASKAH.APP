#!/usr/bin/env python3
"""
Simple startup script for namaskah
"""
import os
import sys
import subprocess

def start_app():
    """Start the namaskah server"""
    print("🚀 Starting namaskah...")
    
    # Check if React build exists
    if not os.path.exists("frontend/build/index.html"):
        print("⚠️  React build not found. Building now...")
        try:
            subprocess.run(["npm", "run", "build"], cwd="frontend", check=True)
            print("✅ React build completed")
        except subprocess.CalledProcessError:
            print("❌ React build failed. Please run: cd frontend && npm run build")
            return False
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js and npm")
            return False
    
    # Start the server
    print("🔄 Starting FastAPI server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_app()