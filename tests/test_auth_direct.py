#!/usr/bin/env python3
"""
Direct test of authentication system without server
"""
import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_auth_direct():
    """Test authentication system directly"""
    print("Testing namaskah Authentication System (Direct)...")

    try:
        # Import required modules
        from auth.security import hash_password, verify_password
        from core.database import (SessionLocal, check_database_connection,
                                   create_tables)
        from services.auth_service import AuthenticationService

        print("✅ All imports successful")

        # Check database
        if not check_database_connection():
            print("❌ Database connection failed")
            return False

        print("✅ Database connection successful")

        # Create tables
        create_tables()
        print("✅ Database tables created/verified")

        # Test authentication service
        db = SessionLocal()
        try:
            auth_service = AuthenticationService(db)

            # Test user registration
            print("\n--- Testing User Registration ---")
            try:
                result = await auth_service.register_user(
                    email="directtest@example.com",
                    username="directtest",
                    password="TestPassword123!",
                    full_name="Direct Test User",
                )
                print(f"✅ User registration successful: {result['user_id']}")
            except Exception as e:
                if "already" in str(e).lower():
                    print("ℹ️  User already exists, continuing with login test")
                else:
                    print(f"❌ User registration failed: {e}")
                    return False

            # Test user authentication
            print("\n--- Testing User Authentication ---")
            try:
                auth_result = await auth_service.authenticate_user(
                    email="directtest@example.com", password="TestPassword123!"
                )
                print(f"✅ User authentication successful")
                print(f"   User: {auth_result['user']['username']}")
                print(f"   Access token length: {len(auth_result['access_token'])}")
                print(f"   Refresh token length: {len(auth_result['refresh_token'])}")

                # Test token refresh
                print("\n--- Testing Token Refresh ---")
                refresh_result = await auth_service.refresh_token(
                    auth_result["refresh_token"]
                )
                print(f"✅ Token refresh successful")
                print(
                    f"   New access token length: {len(refresh_result['access_token'])}"
                )

                # Test API key creation
                print("\n--- Testing API Key Creation ---")
                api_key_result = await auth_service.create_api_key(
                    user_id=auth_result["user"]["id"],
                    name="Direct Test API Key",
                    scopes=["read", "write"],
                )
                print(f"✅ API key creation successful")
                print(f"   API key: {api_key_result['api_key'][:20]}...")

                print("\n🎉 All direct authentication tests passed!")
                return True

            except Exception as e:
                print(f"❌ Authentication test failed: {e}")
                return False

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_auth_direct())
    sys.exit(0 if success else 1)
