#!/usr/bin/env python3
"""
Environment validation for Namaskah.App
Ensures all critical environment variables are present and valid
"""
import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate critical environment variables
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Setup defaults first
    setup_environment_defaults()
    
    errors = []
    
    # Critical variables - app won't work without these
    critical_vars = {
        "JWT_SECRET_KEY": "Authentication will fail completely",
        "DATABASE_URL": "Database connection will fail"
    }
    
    # Optional but important variables
    optional_vars = {
        "TEXTVERIFIED_API_KEY": "SMS verification will use mock mode",
        "TWILIO_ACCOUNT_SID": "Voice calls will be disabled",
        "TWILIO_AUTH_TOKEN": "Voice calls will be disabled",
        "GROQ_API_KEY": "AI features will be disabled",
        "SENTRY_DSN": "Error tracking will be disabled"
    }
    
    # Check critical variables
    for var, impact in critical_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"CRITICAL: {var} is missing - {impact}")
        elif var == "JWT_SECRET_KEY" and len(value) < 32:
            errors.append(f"CRITICAL: {var} is too short (minimum 32 characters)")
    
    # Check optional variables and warn
    warnings = []
    for var, impact in optional_vars.items():
        if not os.getenv(var):
            warnings.append(f"WARNING: {var} is missing - {impact}")
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    # Return validation result
    is_valid = len(errors) == 0
    return is_valid, errors


def get_environment_status() -> Dict[str, any]:
    """Get detailed environment status for health checks"""
    
    critical_vars = ["JWT_SECRET_KEY", "DATABASE_URL"]
    optional_vars = ["TEXTVERIFIED_API_KEY", "TWILIO_ACCOUNT_SID", "GROQ_API_KEY", "SENTRY_DSN"]
    
    status = {
        "critical": {},
        "optional": {},
        "degraded_features": []
    }
    
    # Check critical variables
    for var in critical_vars:
        value = os.getenv(var)
        status["critical"][var] = {
            "present": bool(value),
            "valid": bool(value and len(value) >= 8)
        }
    
    # Check optional variables
    for var in optional_vars:
        status["optional"][var] = bool(os.getenv(var))
    
    # Determine degraded features
    if not os.getenv("TEXTVERIFIED_API_KEY"):
        status["degraded_features"].append("SMS verification (using mock)")
    if not os.getenv("TWILIO_ACCOUNT_SID"):
        status["degraded_features"].append("Voice calls")
    if not os.getenv("GROQ_API_KEY"):
        status["degraded_features"].append("AI assistance")
    if not os.getenv("SENTRY_DSN"):
        status["degraded_features"].append("Error tracking")
    
    return status


def validate_jwt_secret() -> bool:
    """Validate JWT secret key strength"""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        return False
    
    # Check minimum length
    if len(secret) < 32:
        logger.error("JWT_SECRET_KEY is too short (minimum 32 characters)")
        return False
    
    # Check for common weak secrets
    weak_secrets = ["your-secret-key", "secret", "jwt-secret", "change-me"]
    if secret.lower() in weak_secrets:
        logger.error("JWT_SECRET_KEY is using a common weak value")
        return False
    
    return True


def setup_environment_defaults():
    """Set up safe defaults for missing optional environment variables"""
    import secrets
    
    # Generate JWT secret if missing (for deployment environments)
    if not os.getenv("JWT_SECRET_KEY"):
        jwt_secret = secrets.token_urlsafe(32)
        os.environ["JWT_SECRET_KEY"] = jwt_secret
        logger.warning("Generated temporary JWT_SECRET_KEY - set permanent key in production")
    
    # Use SQLite if DATABASE_URL missing
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./namaskah.db"
        logger.info("Using SQLite database (set DATABASE_URL for PostgreSQL)")
    
    defaults = {
        "USE_MOCK_TWILIO": "true",
        "USE_MOCK_TEXTVERIFIED": "true", 
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "CORS_ORIGINS": "*",
        "RATE_LIMIT_ENABLED": "true"
    }
    
    for key, default_value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            logger.info(f"Set default {key}={default_value}")