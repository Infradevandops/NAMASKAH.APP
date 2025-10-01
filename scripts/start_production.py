#!/usr/bin/env python3
"""
Production startup script with environment validation and graceful fallbacks.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_default_env_vars():
    """Set default environment variables if not provided."""
    defaults = {
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRE_MINUTES': '30',
        'LOG_LEVEL': 'INFO',
        'USE_MOCK_TWILIO': 'true',
        'DEBUG': 'false',
        'CORS_ORIGINS': 'https://*.onrender.com,https://*.herokuapp.com',
        'RATE_LIMIT_PER_MINUTE': '60'
    }
    
    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value
            logger.info(f"Set default {key}={value}")

def validate_critical_env_vars():
    """Validate critical environment variables."""
    critical_vars = ['JWT_SECRET_KEY']
    
    missing = []
    for var in critical_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Critical environment variables missing: {missing}")
        logger.error("Please set these variables before starting the application.")
        return False
    
    return True

def setup_database_url():
    """Setup database URL with fallback to SQLite."""
    if not os.getenv('DATABASE_URL'):
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        sqlite_path = data_dir / 'namaskah_app.db'
        database_url = f'sqlite:///{sqlite_path}'
        os.environ['DATABASE_URL'] = database_url
        logger.info(f"Using SQLite database: {database_url}")

def main():
    """Main startup function."""
    logger.info("🚀 Starting CumApp in production mode...")
    
    # Set default environment variables
    set_default_env_vars()
    
    # Validate critical environment variables
    if not validate_critical_env_vars():
        sys.exit(1)
    
    # Setup database URL
    setup_database_url()
    
    # Log configuration
    logger.info("📋 Configuration:")
    logger.info(f"  PORT: {os.getenv('PORT', '8000')}")
    logger.info(f"  DEBUG: {os.getenv('DEBUG')}")
    logger.info(f"  USE_MOCK_TWILIO: {os.getenv('USE_MOCK_TWILIO')}")
    logger.info(f"  DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    
    # Import and start the application
    try:
        logger.info("📦 Importing application...")
        from main import app
        logger.info("✅ Application imported successfully")
        
        # Start with uvicorn
        import uvicorn
        
        port = int(os.getenv('PORT', 8000))
        host = '0.0.0.0'
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=os.getenv('LOG_LEVEL', 'info').lower(),
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()