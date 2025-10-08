#!/usr/bin/env python3
"""
Database reset script for Namaskah.App
Use with caution - this will drop all tables and recreate them
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def drop_all_tables():
    """Drop all existing tables"""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("No tables to drop")
            return True
        
        logger.info(f"Dropping {len(existing_tables)} tables...")
        
        with engine.connect() as conn:
            # Disable foreign key constraints temporarily
            if "sqlite" in str(engine.url):
                conn.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Drop all tables
            for table_name in existing_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    logger.info(f"Dropped table: {table_name}")
                except Exception as e:
                    logger.warning(f"Could not drop table {table_name}: {e}")
            
            conn.commit()
            
            # Re-enable foreign key constraints
            if "sqlite" in str(engine.url):
                conn.execute(text("PRAGMA foreign_keys = ON"))
        
        logger.info("✅ All tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False


def create_fresh_tables():
    """Create fresh tables"""
    try:
        logger.info("Creating fresh database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify creation
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        expected_tables = list(Base.metadata.tables.keys())
        
        missing_tables = set(expected_tables) - set(created_tables)
        if missing_tables:
            logger.error(f"Failed to create tables: {missing_tables}")
            return False
        
        logger.info(f"✅ Successfully created {len(created_tables)} tables")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def main():
    """Main reset function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        confirmed = True
    else:
        print("⚠️  WARNING: This will delete ALL data in the database!")
        print("This action cannot be undone.")
        print("")
        response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
        confirmed = response.lower() == 'yes'
    
    if not confirmed:
        print("Database reset cancelled.")
        return
    
    logger.info("🔄 Starting database reset...")
    
    # Step 1: Drop all tables
    if not drop_all_tables():
        logger.error("❌ Failed to drop tables")
        sys.exit(1)
    
    # Step 2: Create fresh tables
    if not create_fresh_tables():
        logger.error("❌ Failed to create fresh tables")
        sys.exit(1)
    
    logger.info("🎉 Database reset completed successfully!")
    print("")
    print("✅ Database has been reset with fresh tables")
    print("🔧 You may want to run the admin user creation script:")
    print("   python create_admin_user.py")


if __name__ == "__main__":
    main()