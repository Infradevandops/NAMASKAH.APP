"""
Production configuration and environment setup.
"""
import os
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ProductionConfig:
    """Production environment configuration."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.secret_key = os.getenv("SECRET_KEY")
        
        # Validate required production settings
        if self.environment == "production":
            self._validate_production_config()
    
    def _validate_production_config(self):
        """Validate required production configuration."""
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "SENTRY_DSN"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required production environment variables: {', '.join(missing_vars)}")
        
        # Validate secret key strength
        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for production")
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Database configuration."""
        return {
            "url": os.getenv("DATABASE_URL"),
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """Redis configuration."""
        return {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Security configuration."""
        return {
            "cors_origins": self._parse_list(os.getenv("CORS_ORIGINS", "[]")),
            "allowed_hosts": self._parse_list(os.getenv("ALLOWED_HOSTS", "[]")),
            "secure_ssl_redirect": os.getenv("SECURE_SSL_REDIRECT", "false").lower() == "true",
            "session_cookie_secure": os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
            "csrf_cookie_secure": os.getenv("CSRF_COOKIE_SECURE", "false").lower() == "true",
        }
    
    @property
    def sentry_config(self) -> Dict[str, Any]:
        """Sentry configuration."""
        return {
            "dsn": os.getenv("SENTRY_DSN"),
            "environment": os.getenv("SENTRY_ENVIRONMENT", self.environment),
            "traces_sample_rate": float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            "profiles_sample_rate": float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            "enable_tracing": True,
            "attach_stacktrace": True,
            "send_default_pii": False,
        }
    
    @property
    def performance_config(self) -> Dict[str, Any]:
        """Performance monitoring configuration."""
        return {
            "enabled": os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true",
            "sample_rate": float(os.getenv("PERFORMANCE_SAMPLE_RATE", "0.1")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
    
    @property
    def rate_limiting_config(self) -> Dict[str, Any]:
        """Rate limiting configuration."""
        return {
            "enabled": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            "requests_per_minute": int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100")),
            "burst": int(os.getenv("RATE_LIMIT_BURST", "20")),
        }
    
    @property
    def health_check_config(self) -> Dict[str, Any]:
        """Health check configuration."""
        return {
            "enabled": os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true",
            "interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            "timeout": int(os.getenv("HEALTH_CHECK_TIMEOUT", "10")),
        }
    
    @property
    def backup_config(self) -> Dict[str, Any]:
        """Backup configuration."""
        return {
            "enabled": os.getenv("BACKUP_ENABLED", "false").lower() == "true",
            "schedule": os.getenv("BACKUP_SCHEDULE", "0 2 * * *"),
            "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            "storage_path": os.getenv("BACKUP_STORAGE_PATH", "/backups"),
        }
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Logging configuration."""
        return {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": os.getenv("LOG_FILE_PATH", "/var/log/namaskah/app.log"),
            "max_bytes": int(os.getenv("LOG_MAX_BYTES", "10485760")),  # 10MB
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
        }
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list."""
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return [item.strip() for item in value.split(",") if item.strip()]
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": self.database_config,
            "redis": self.redis_config,
            "security": self.security_config,
            "sentry": self.sentry_config,
            "performance": self.performance_config,
            "rate_limiting": self.rate_limiting_config,
            "health_check": self.health_check_config,
            "backup": self.backup_config,
            "logging": self.logging_config,
        }


# Global configuration instance
config = ProductionConfig()


def setup_production_logging():
    """Set up production logging configuration."""
    log_config = config.logging_config
    
    # Create log directory if it doesn't exist
    log_file = Path(log_config["file_path"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config["level"]),
        format=log_config["format"],
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.handlers.RotatingFileHandler(
                log_config["file_path"],
                maxBytes=log_config["max_bytes"],
                backupCount=log_config["backup_count"]
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger.info(f"Production logging configured - Level: {log_config['level']}")


def validate_production_environment():
    """Validate production environment setup."""
    logger.info("Validating production environment...")
    
    checks = []
    
    # Check database connection
    try:
        from core.database import check_database_connection
        db_ok = check_database_connection()
        checks.append(("Database Connection", db_ok))
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks.append(("Database Connection", False))
    
    # Check Redis connection
    try:
        import redis
        redis_client = redis.from_url(config.redis_config["url"])
        redis_client.ping()
        checks.append(("Redis Connection", True))
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        checks.append(("Redis Connection", False))
    
    # Check Sentry configuration
    sentry_ok = bool(config.sentry_config["dsn"])
    checks.append(("Sentry Configuration", sentry_ok))
    
    # Check SSL/Security settings
    security_ok = config.security_config["secure_ssl_redirect"] if config.environment == "production" else True
    checks.append(("Security Settings", security_ok))
    
    # Report results
    failed_checks = [name for name, status in checks if not status]
    
    if failed_checks:
        logger.warning(f"Failed production checks: {', '.join(failed_checks)}")
        return False
    else:
        logger.info("✅ All production environment checks passed")
        return True


def get_deployment_info() -> Dict[str, Any]:
    """Get deployment information."""
    return {
        "environment": config.environment,
        "debug": config.debug,
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "build_date": os.getenv("BUILD_DATE"),
        "commit_hash": os.getenv("COMMIT_HASH"),
        "deployment_date": os.getenv("DEPLOYMENT_DATE"),
        "health_checks_enabled": config.health_check_config["enabled"],
        "performance_monitoring": config.performance_config["enabled"],
        "sentry_enabled": bool(config.sentry_config["dsn"]),
    }