"""
Sentry configuration for error tracking and performance monitoring.
"""
import os
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry SDK with comprehensive integrations."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "production"))
    
    # Debug environment variables
    logger.info(f"🔍 Environment check - SENTRY_DSN present: {bool(sentry_dsn)}")
    logger.info(f"🔍 Environment: {environment}")
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not found. Sentry error tracking disabled.")
        logger.info("Available env vars: " + ", ".join([k for k in os.environ.keys() if 'SENTRY' in k]))
        return False

    try:
        # Get configuration from environment
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
        profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
        
        # Adjust sample rates for development
        if environment == "development":
            traces_sample_rate = 1.0
            profiles_sample_rate = 1.0
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            
            integrations=[
                # FastAPI integration
                FastApiIntegration(
                    transaction_style="endpoint"
                ),
                
                # Database integration
                SqlalchemyIntegration(),
                
                # Redis integration
                RedisIntegration(),
                
                # Logging integration
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
                
                # Asyncio integration
                AsyncioIntegration(),
            ],
            
            # Performance monitoring
            enable_tracing=True,
            attach_stacktrace=True,
            
            # Privacy settings
            send_default_pii=False,
            
            # Custom transaction filtering
            before_send_transaction=filter_transactions,
            
            # Custom error filtering
            before_send=filter_errors,
            
            # Release tracking
            release=os.getenv("APP_VERSION", "1.0.0"),
            
            # Additional options
            max_breadcrumbs=50,
            debug=environment == "development",
        )
        
        # Set user context if available
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("service", "namaskah")
            scope.set_tag("component", "backend")
            
        logger.info(f"✅ Sentry initialized successfully - Environment: {environment}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")
        return False


def filter_transactions(transaction, hint):
    """Filter transactions before sending to Sentry."""
    transaction_name = transaction.get("name", "")
    
    # Skip health check endpoints (reduce noise)
    if transaction_name.startswith("/health"):
        return None
    
    # Skip static file requests
    if any(static in transaction_name for static in ["/static/", "/favicon.ico", "/robots.txt"]):
        return None
    
    # Skip successful OPTIONS requests
    if transaction.get("request", {}).get("method") == "OPTIONS":
        return None
    
    return transaction


def filter_errors(event, hint):
    """Filter errors before sending to Sentry."""
    # Skip certain HTTP errors that are not actionable
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        
        # Skip common HTTP errors
        if hasattr(exc_value, "status_code"):
            status_code = exc_value.status_code
            if status_code in [400, 401, 403, 404, 422]:
                return None
    
    # Skip database connection errors during startup
    if "database" in str(event.get("message", "")).lower():
        if "startup" in str(event.get("contexts", {})):
            return None
    
    return event


def get_sentry_user_context(request):
    """Extract user context from request for Sentry."""
    user = getattr(request.state, "user", None)
    if user:
        return {
            "id": user.get("id"),
            "email": user.get("email"),
            "username": user.get("username"),
        }
    return None


def capture_custom_metric(name, value, tags=None):
    """Capture custom performance metrics."""
    if sentry_sdk.Hub.current.scope:
        sentry_sdk.Hub.current.scope.set_tag("custom_metric", name)
        sentry_sdk.Hub.current.scope.set_measurement(name, value)
        if tags:
            for key, tag_value in tags.items():
                sentry_sdk.Hub.current.scope.set_tag(key, tag_value)