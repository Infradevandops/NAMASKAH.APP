#!/usr/bin/env python3
"""
Initialize database with default users and data
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from core.database import SessionLocal, create_tables, check_database_connection
from models.user_models import User
from auth.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_default_users(db: Session):
    """Create default users for testing"""
    
    # Check if admin user already exists
    admin_user = db.query(User).filter(User.email == "admin@namaskah.app").first()
    if admin_user:
        logger.info("Admin user already exists")
        return
    
    # Create admin user
    admin_user = User(
        email="admin@namaskah.app",
        username="admin",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        role="admin"
    )
    
    db.add(admin_user)
    
    # Create demo user
    demo_user = User(
        email="demo@namaskah.app",
        username="demo",
        hashed_password=hash_password("demo123"),
        full_name="Demo User",
        is_active=True,
        is_verified=True,
        role="user"
    )
    
    db.add(demo_user)
    
    # Create test user
    test_user = User(
        email="test@namaskah.app",
        username="test", 
        hashed_password=hash_password("test123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role="user"
    )
    
    db.add(test_user)
    
    db.commit()
    
    logger.info("✅ Default users created:")
    logger.info("   Admin: admin@namaskah.app / admin123")
    logger.info("   Demo:  demo@namaskah.app / demo123")
    logger.info("   Test:  test@namaskah.app / test123")


def main():
    """Initialize database"""
    logger.info("🚀 Initializing namaskah Database...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("❌ Database connection failed")
        return False
    
    try:
        # Create tables
        logger.info("📋 Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created")
        
        # Create default users
        logger.info("👥 Creating default users...")
        db = SessionLocal()
        try:
            create_default_users(db)
        finally:
            db.close()
        
        logger.info("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)