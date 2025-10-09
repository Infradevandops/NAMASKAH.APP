#!/usr/bin/env python3
"""
Test script to verify the server is working correctly
"""
import subprocess
import time
import requests
import sys
import os

def test_server():
    """Test if the server starts and responds correctly"""
    print("🚀 Testing namaskah Server...")
    
    # Check if React build exists
    if os.path.exists("frontend/build/index.html"):
        print("✅ React build found")
    else:
        print("❌ React build not found - run: cd frontend && npm run build")
        return False
    
    try:
        # Start server in background
        print("🔄 Starting server...")
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test endpoints
        base_url = "http://localhost:8000"
        
        print("🧪 Testing endpoints...")
        
        # Test health check
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health check working")
            else:
                print(f"⚠️  Health check returned {response.status_code}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test root route
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200 and "namaskah" in response.text:
                print("✅ Root route working")
            else:
                print(f"⚠️  Root route returned {response.status_code}")
        except Exception as e:
            print(f"❌ Root route failed: {e}")
        
        # Test API docs
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("✅ API docs working")
            else:
                print(f"⚠️  API docs returned {response.status_code}")
        except Exception as e:
            print(f"❌ API docs failed: {e}")
        
        print("\n🎉 Server test completed!")
        print(f"🌐 Access your app at: {base_url}")
        print(f"📖 API docs at: {base_url}/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False
    finally:
        # Clean up
        if 'server_process' in locals():
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    test_server()