#!/usr/bin/env python3
"""
Comprehensive Authentication Feature Testing Script
Tests: Sign up, Login, Logout, and Google OAuth 2.0
"""
import asyncio
import json
import os
import sys
import time
from typing import Dict, Any

import httpx
import uvicorn
from fastapi import FastAPI
from multiprocessing import Process

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AuthTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.test_results = []
        
    async def test_health_check(self):
        """Test if the server is running"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_result("✅ Health Check", "Server is running", response.json())
                return True
            else:
                self.log_result("❌ Health Check", f"Server returned {response.status_code}", None)
                return False
        except Exception as e:
            self.log_result("❌ Health Check", f"Server not accessible: {e}", None)
            return False
    
    async def test_user_registration(self):
        """Test user registration endpoint"""
        test_user = {
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/register",
                json=test_user
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log_result("✅ User Registration", "User registered successfully", data)
                return True, data
            else:
                self.log_result("❌ User Registration", f"Failed with status {response.status_code}", response.text)
                return False, None
                
        except Exception as e:
            self.log_result("❌ User Registration", f"Exception: {e}", None)
            return False, None
    
    async def test_user_login(self, email: str = "testuser@example.com", password: str = "TestPassword123!"):
        """Test user login endpoint"""
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("✅ User Login", "Login successful", {
                    "token_type": data.get("token_type"),
                    "user_email": data.get("user", {}).get("email"),
                    "user_role": data.get("user", {}).get("role")
                })
                return True, data
            else:
                self.log_result("❌ User Login", f"Failed with status {response.status_code}", response.text)
                return False, None
                
        except Exception as e:
            self.log_result("❌ User Login", f"Exception: {e}", None)
            return False, None
    
    async def test_protected_endpoint(self, access_token: str):
        """Test accessing protected endpoint with token"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("✅ Protected Endpoint", "Access granted with valid token", data)
                return True, data
            else:
                self.log_result("❌ Protected Endpoint", f"Access denied with status {response.status_code}", response.text)
                return False, None
                
        except Exception as e:
            self.log_result("❌ Protected Endpoint", f"Exception: {e}", None)
            return False, None
    
    async def test_logout(self, refresh_token: str = None):
        """Test user logout endpoint"""
        if not refresh_token:
            # Mock logout test since we might not have refresh token
            self.log_result("⚠️ User Logout", "Skipped - No refresh token available", None)
            return True, None
            
        logout_data = {"refresh_token": refresh_token}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/logout",
                json=logout_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("✅ User Logout", "Logout successful", data)
                return True, data
            else:
                self.log_result("❌ User Logout", f"Failed with status {response.status_code}", response.text)
                return False, None
                
        except Exception as e:
            self.log_result("❌ User Logout", f"Exception: {e}", None)
            return False, None
    
    async def test_google_oauth_setup(self):
        """Test Google OAuth 2.0 setup and availability"""
        # Check if Google OAuth endpoints exist
        oauth_endpoints = [
            "/api/auth/google/login",
            "/api/auth/google/callback",
            "/api/auth/google/token"
        ]
        
        oauth_available = False
        
        for endpoint in oauth_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code != 404:
                    oauth_available = True
                    break
            except:
                continue
        
        if oauth_available:
            self.log_result("✅ Google OAuth 2.0", "OAuth endpoints available", {"endpoints": oauth_endpoints})
        else:
            self.log_result("❌ Google OAuth 2.0", "OAuth endpoints not implemented", {
                "note": "Google OAuth 2.0 needs to be implemented",
                "required_endpoints": oauth_endpoints
            })
        
        return oauth_available
    
    async def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json=invalid_login
            )
            
            if response.status_code == 401:
                self.log_result("✅ Invalid Credentials", "Correctly rejected invalid login", None)
                return True
            else:
                self.log_result("❌ Invalid Credentials", f"Unexpected status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("❌ Invalid Credentials", f"Exception: {e}", None)
            return False
    
    async def test_duplicate_registration(self):
        """Test registering with existing email"""
        duplicate_user = {
            "email": "testuser@example.com",  # Same as first registration
            "password": "AnotherPassword123!"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/register",
                json=duplicate_user
            )
            
            if response.status_code == 400:
                self.log_result("✅ Duplicate Registration", "Correctly rejected duplicate email", None)
                return True
            else:
                self.log_result("❌ Duplicate Registration", f"Unexpected status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("❌ Duplicate Registration", f"Exception: {e}", None)
            return False
    
    def log_result(self, test_name: str, message: str, data: Any):
        """Log test result"""
        result = {
            "test": test_name,
            "message": message,
            "data": data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        print(f"{test_name}: {message}")
        if data:
            print(f"  Data: {json.dumps(data, indent=2)}")
        print()
    
    async def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Comprehensive Authentication Tests")
        print("=" * 60)
        
        # 1. Health Check
        if not await self.test_health_check():
            print("❌ Server not accessible. Please start the server first.")
            return
        
        # 2. User Registration
        reg_success, reg_data = await self.test_user_registration()
        
        # 3. User Login
        login_success, login_data = await self.test_user_login()
        access_token = login_data.get("access_token") if login_data else None
        refresh_token = login_data.get("refresh_token") if login_data else None
        
        # 4. Protected Endpoint Access
        if access_token:
            await self.test_protected_endpoint(access_token)
        
        # 5. User Logout
        await self.test_logout(refresh_token)
        
        # 6. Google OAuth 2.0
        await self.test_google_oauth_setup()
        
        # 7. Security Tests
        await self.test_invalid_credentials()
        await self.test_duplicate_registration()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r["test"].startswith("✅")])
        failed = len([r for r in self.test_results if r["test"].startswith("❌")])
        warnings = len([r for r in self.test_results if r["test"].startswith("⚠️")])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"📝 Total Tests: {len(self.test_results)}")
        
        if failed == 0:
            print("\n🎉 All critical tests passed!")
        else:
            print(f"\n⚠️ {failed} tests failed - review implementation")
        
        # Save results to file
        with open("auth_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: auth_test_results.json")

def start_server():
    """Start the FastAPI server"""
    try:
        # Import and run the main app
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"Failed to start server: {e}")

async def main():
    """Main test function"""
    # Check if server is already running
    tester = AuthTester()
    
    try:
        response = await tester.client.get("http://localhost:8000/health")
        server_running = response.status_code == 200
    except:
        server_running = False
    
    if not server_running:
        print("🚀 Starting server...")
        # Start server in background
        server_process = Process(target=start_server)
        server_process.start()
        
        # Wait for server to start
        for i in range(10):
            try:
                response = await tester.client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("✅ Server started successfully")
                    break
            except:
                pass
            await asyncio.sleep(2)
            print(f"⏳ Waiting for server... ({i+1}/10)")
        else:
            print("❌ Failed to start server")
            return
    else:
        print("✅ Server already running")
    
    # Run tests
    await tester.run_all_tests()
    
    # Cleanup
    await tester.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())