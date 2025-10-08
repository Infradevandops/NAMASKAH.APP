#!/usr/bin/env python3
"""
Google OAuth 2.0 Test Script
"""
import os
import sys
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleOAuthTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
    
    def check_environment(self):
        """Check if Google OAuth is configured"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        print("🔍 Checking Google OAuth Configuration...")
        print(f"Client ID: {client_id[:20]}...{client_id[-20:] if client_id else 'NOT SET'}")
        print(f"Client Secret: {'SET' if client_secret and client_secret != 'your_google_client_secret_here' else 'NOT SET'}")
        print(f"Redirect URI: {redirect_uri}")
        print()
        
        if not client_id:
            print("❌ GOOGLE_CLIENT_ID not set")
            return False
        
        if not client_secret or client_secret == 'your_google_client_secret_here':
            print("❌ GOOGLE_CLIENT_SECRET not set properly")
            print("   Go to Google Cloud Console and get your Client Secret")
            return False
        
        if not redirect_uri:
            print("❌ GOOGLE_REDIRECT_URI not set")
            return False
        
        print("✅ Environment variables configured")
        return True
    
    async def test_config_endpoint(self):
        """Test Google OAuth config endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/auth/google/config")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Config endpoint working")
                    print(f"   Configured: {data.get('configured')}")
                    print(f"   Setup required: {data.get('setup_required')}")
                    return data.get('configured', False)
                else:
                    print(f"❌ Config endpoint failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Config endpoint error: {e}")
            return False
    
    async def test_login_endpoint(self):
        """Test Google OAuth login endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/auth/google/login")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'auth_url' in data:
                        print("✅ Login endpoint working")
                        print(f"   Auth URL generated: {data['auth_url'][:50]}...")
                        return True
                    else:
                        print("❌ Login endpoint missing auth_url")
                        return False
                elif response.status_code == 501:
                    data = response.json()
                    print("⚠️  OAuth not configured")
                    print(f"   Error: {data.get('detail', {}).get('error')}")
                    return False
                else:
                    print(f"❌ Login endpoint failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Login endpoint error: {e}")
            return False
    
    async def test_server_running(self):
        """Test if server is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5)
                
                if response.status_code == 200:
                    print("✅ Server is running")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print("❌ Server not running")
            print("   Start with: source .venv/bin/activate && python -m uvicorn main:app --reload")
            return False
    
    async def run_tests(self):
        """Run all Google OAuth tests"""
        print("🚀 Google OAuth 2.0 Test Suite")
        print("=" * 40)
        print()
        
        # 1. Check environment
        env_ok = self.check_environment()
        
        # 2. Check server
        server_ok = await self.test_server_running()
        
        if not server_ok:
            print("\n❌ Cannot test endpoints - server not running")
            return
        
        # 3. Test config endpoint
        config_ok = await self.test_config_endpoint()
        
        # 4. Test login endpoint
        login_ok = await self.test_login_endpoint()
        
        # Summary
        print("\n" + "=" * 40)
        print("📊 TEST SUMMARY")
        print("=" * 40)
        
        if env_ok and config_ok and login_ok:
            print("🎉 Google OAuth 2.0 is FULLY WORKING!")
            print("\n🔗 Test in browser:")
            print(f"   {self.base_url}/api/auth/google/login")
        elif env_ok and server_ok:
            print("⚠️  Google OAuth partially working")
            print("   Check your Client Secret")
        else:
            print("❌ Google OAuth needs configuration")
            print("\n📋 TODO:")
            if not env_ok:
                print("   1. Set GOOGLE_CLIENT_SECRET in .env")
            if not server_ok:
                print("   2. Start the server")

def main():
    tester = GoogleOAuthTester()
    asyncio.run(tester.run_tests())

if __name__ == "__main__":
    main()