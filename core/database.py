#!/usr/bin/env python3
"""
Database configuration and session management for namaskah
Enhanced with PostgreSQL support and connection pooling
"""
import logging
import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Database URL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./namaskah.db"  # Default to SQLite for development
)

# Handle PostgreSQL URL format for production
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
else:
    # PostgreSQL configuration for production
    try:
        from config.postgresql_config import postgresql_config
        engine = postgresql_config.create_engine()
        SessionLocal = postgresql_config.get_session_factory(engine)
        
        # Validate connection on startup
        if not postgresql_config.validate_connection(engine):
            logger.error("PostgreSQL connection validation failed")
            raise ConnectionError("Failed to connect to PostgreSQL")
        
        logger.info("PostgreSQL connection established successfully")
        
    except ImportError:
        logger.warning("PostgreSQL config not available, using basic configuration")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    """
    try:
        # Import all models here to ensure they are registered with Base
        from models import (communication_models, conversation_models,
                            enhanced_models, phone_number_models,
                            subscription_models, user_models,
                            verification_models)

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
