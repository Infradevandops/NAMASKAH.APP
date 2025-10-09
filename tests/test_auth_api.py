#!/usr/bin/env python3
"""
Test script for authentication API endpoints
"""
import asyncio
import json

import httpx

BASE_URL = "http://localhost:8001"


async def test_auth_api():
    """Test the authentication API endpoints"""
    print("Testing namaskah Authentication API...")

    async with httpx.AsyncClient() as client:
        try:
            # Test health check
            response = await client.get(f"{BASE_URL}/api/auth/health")
            if response.status_code == 200:
                print("✅ Auth health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Auth health check failed: {response.status_code}")
                return

            # Test user registration
            registration_data = {
                "email": "testuser@example.com",
                "username": "testuser123",
                "password": "TestPassword123!",
                "full_name": "Test User",
            }

            response = await client.post(
                f"{BASE_URL}/api/auth/register", json=registration_data
            )

            if response.status_code == 201:
                print("✅ User registration successful")
                reg_result = response.json()
                print(f"   User ID: {reg_result['user_id']}")
                print(f"   Username: {reg_result['username']}")
            else:
                print(f"❌ User registration failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return

            # Test user login
            login_data = {
                "email": "testuser@example.com",
                "password": "TestPassword123!",
            }

            response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)

            if response.status_code == 200:
                print("✅ User login successful")
                login_result = response.json()
                access_token = login_result["access_token"]
                refresh_token = login_result["refresh_token"]
                print(f"   Access token received (length: {len(access_token)})")
                print(f"   User: {login_result['user']['username']}")
            else:
                print(f"❌ User login failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return

            # Test protected endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(f"{BASE_URL}/api/auth/me", headers=headers)

            if response.status_code == 200:
                print("✅ Protected endpoint access successful")
                user_info = response.json()
                print(f"   User info: {user_info['username']} ({user_info['email']})")
            else:
                print(f"❌ Protected endpoint access failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return

            # Test token refresh
            refresh_data = {"refresh_token": refresh_token}
            response = await client.post(
                f"{BASE_URL}/api/auth/refresh", json=refresh_data
            )

            if response.status_code == 200:
                print("✅ Token refresh successful")
                refresh_result = response.json()
                new_access_token = refresh_result["access_token"]
                print(f"   New access token received (length: {len(new_access_token)})")
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Error: {response.text}")

            # Test API key creation
            api_key_data = {"name": "Test API Key", "scopes": ["read", "write"]}

            response = await client.post(
                f"{BASE_URL}/api/auth/api-keys", json=api_key_data, headers=headers
            )

            if response.status_code == 200:
                print("✅ API key creation successful")
                api_key_result = response.json()
                api_key = api_key_result["api_key"]
                print(f"   API key created: {api_key[:20]}...")

                # Test API key authentication
                api_headers = {"Authorization": f"Bearer {api_key}"}
                response = await client.get(
                    f"{BASE_URL}/api/auth/me", headers=api_headers
                )

                if response.status_code == 200:
                    print("✅ API key authentication successful")
                else:
                    print(f"❌ API key authentication failed: {response.status_code}")
            else:
                print(f"❌ API key creation failed: {response.status_code}")
                print(f"   Error: {response.text}")

            print("\n🎉 All authentication API tests completed!")

        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_auth_api())
