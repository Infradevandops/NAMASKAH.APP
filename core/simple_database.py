#!/usr/bin/env python3
"""
Simple database initialization for production deployment
"""
import logging
from sqlalchemy.exc import SQLAlchemyError
from core.database import engine, Base

logger = logging.getLogger(__name__)


def simple_create_tables():
    """Simple table creation without complex validation"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("✅ Database tables created successfully")
        return True, ["Database tables created successfully"]
    except SQLAlchemyError as e:
        if "already exists" in str(e).lower():
            logger.info("✅ Database tables already exist")
            return True, ["Database tables already exist"]
        else:
            logger.error(f"Database creation failed: {e}")
            return False, [f"Database creation failed: {str(e)}"]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, [f"Unexpected error: {str(e)}"]