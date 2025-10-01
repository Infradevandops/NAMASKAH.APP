"""
Configuration management for CumApp
"""

import os
from typing import Any, Dict


class Config:
    """Base configuration class"""
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'CumApp')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', 8000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', 30))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./namaskah.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
    
    # External APIs
    TEXTVERIFIED_API_KEY = os.getenv('TEXTVERIFIED_API_KEY')
    TEXTVERIFIED_EMAIL = os.getenv('TEXTVERIFIED_EMAIL')
    
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
    
    # Service toggles
    USE_MOCK_TWILIO = os.getenv('USE_MOCK_TWILIO', 'true').lower() == 'true'
    USE_MOCK_TEXTVERIFIED = os.getenv('USE_MOCK_TEXTVERIFIED', 'true').lower() == 'true'
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    REQUESTS_PER_MINUTE = int(os.getenv('REQUESTS_PER_MINUTE', 100))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_URL = 'sqlite:///./namaskah_dev.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use environment variables for production


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    DATABASE_URL = 'sqlite:///./test.db'
    JWT_SECRET_KEY = 'test-secret-key'


def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Global config instance
config = get_config()