#!/usr/bin/env python3
"""
Diagnostic script to check what's wrong with the server
"""
import os
import sys

def diagnose():
    """Run diagnostics on the namaskah setup"""
    print("🔍 namaskah Diagnostics")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check if main.py exists
    if os.path.exists("main.py"):
        print("✅ main.py exists")
    else:
        print("❌ main.py not found")
        return
    
    # Check if React build exists
    if os.path.exists("frontend/build/index.html"):
        print("✅ React build exists")
        
        # Check file size
        size = os.path.getsize("frontend/build/index.html")
        print(f"   index.html size: {size} bytes")
        
        # Check static files
        if os.path.exists("frontend/build/static"):
            print("✅ Static files directory exists")
        else:
            print("❌ Static files directory missing")
    else:
        print("❌ React build not found")
    
    # Try importing main module
    print("\n🧪 Testing imports...")
    try:
        sys.path.append('.')
        import main
        print("✅ main.py imports successfully")
        
        # Check if app is defined
        if hasattr(main, 'app'):
            print("✅ FastAPI app is defined")
        else:
            print("❌ FastAPI app not found in main.py")
            
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check required packages
    print("\n📦 Checking packages...")
    required_packages = ['fastapi', 'uvicorn', 'jinja2']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} not installed")
    
    print("\n" + "=" * 50)
    print("Diagnosis complete!")

if __name__ == "__main__":
    diagnose()