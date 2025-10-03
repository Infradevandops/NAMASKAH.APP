#!/usr/bin/env python3
"""
Create test user for local development
"""
import os
import asyncio
from dotenv import load_dotenv

# Load local environment
load_dotenv('.env.local')

from core.database import get_db_session, create_tables
from models.user_models import User
from auth.security import get_password_hash

async def create_test_user():
    """Create a test user for local development"""
    
    # Ensure database exists
    create_tables()
    
    # Test user credentials
    test_email = "test@namaskah.app"
    test_password = "TestPassword123!"
    test_username = "testuser"
    
    # Create database session
    db = next(get_db_session())
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == test_email).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {test_email}")
            print(f"   Username: {existing_user.username}")
            print(f"   User ID: {existing_user.id}")
            return existing_user
        
        # Create new test user
        hashed_password = get_password_hash(test_password)
        
        test_user = User(
            email=test_email,
            username=test_username,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            credits=1000  # Give test user some credits
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Created test user successfully!")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   Username: {test_username}")
        print(f"   User ID: {test_user.id}")
        print(f"   Credits: {test_user.credits}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())