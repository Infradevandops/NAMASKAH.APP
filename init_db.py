#!/usr/bin/env python3
"""
Database initialization script
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        print("Initializing Namaskah.App database...")

        # Import and test database connection
        from core.database import check_database_connection, create_tables

        if not check_database_connection():
            print("Database connection failed!")
            return False

        print("Database connection successful!")

        # Create tables
        create_tables()
        print("Database tables created successfully!")

        # Test authentication imports
        from auth.security import hash_password, verify_password
        from services.auth_service import AuthenticationService

        print("Authentication system imported successfully!")

        # Test password hashing
        test_password = "TestPassword123!"
        hashed = hash_password(test_password)
        if verify_password(test_password, hashed):
            print("Password hashing test passed!")
        else:
            print("Password hashing test failed!")
            return False

        print("✅ Database initialization completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
