#!/usr/bin/env python3
"""
Simple test script for authentication system
"""
import asyncio
import sys
import traceback

try:
    from auth.security import hash_password, verify_password
    from core.database import (SessionLocal, check_database_connection,
                               create_tables)
    from services.auth_service import AuthenticationService

    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()
    sys.exit(1)


async def test_authentication():
    """Test the authentication system"""
    print("Testing namaskah Authentication System...")

    # Check database connection
    if not check_database_connection():
        print("❌ Database connection failed!")
        return
    print("✅ Database connection successful")

    # Create tables
    try:
        create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        return

    # Test password hashing
    test_password = "TestPassword123!"
    hashed = hash_password(test_password)
    if verify_password(test_password, hashed):
        print("✅ Password hashing works correctly")
    else:
        print("❌ Password hashing failed")
        return

    # Test user registration
    db = SessionLocal()
    try:
        auth_service = AuthenticationService(db)

        # Register a test user
        result = await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            full_name="Test User",
        )
        print(f"✅ User registration successful: {result['user_id']}")

        # Test authentication
        auth_result = await auth_service.authenticate_user(
            email="test@example.com", password="TestPassword123!"
        )
        print(f"✅ User authentication successful: {auth_result['user']['username']}")

        # Test token refresh
        refresh_result = await auth_service.refresh_token(auth_result["refresh_token"])
        print("✅ Token refresh successful")

        print("\n🎉 All authentication tests passed!")

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_authentication())
