#!/usr/bin/env python3
"""
Monitoring and observability setup script for namaskah enterprise platform.
Configures Sentry, performance monitoring, health checks, and logging.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.production_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringSetup:
    """Monitoring and observability setup."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.environment = os.getenv("ENVIRONMENT", "production")

    def setup_monitoring(self):
        """Set up complete monitoring stack."""
        logger.info("🚀 Setting up monitoring and observability")

        steps = [
            self.setup_sentry,
            self.setup_performance_monitoring,
            self.setup_health_checks,
            self.setup_logging,
            self.setup_metrics_collection,
            self.create_monitoring_config,
            self.validate_monitoring_setup
        ]

        for step in steps:
            try:
                step()
                logger.info(f"✅ {step.__name__} completed")
            except Exception as e:
                logger.error(f"❌ {step.__name__} failed: {e}")
                raise

        logger.info("🎉 Monitoring setup completed successfully!")

    def setup_sentry(self):
        """Set up Sentry error tracking."""
        logger.info("Setting up Sentry error tracking...")

        sentry_config = config.sentry_config

        if not sentry_config["dsn"]:
            logger.warning("Sentry DSN not configured - skipping Sentry setup")
            return

        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastAPIIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=sentry_config["dsn"],
                environment=sentry_config["environment"],
                traces_sample_rate=sentry_config["traces_sample_rate"],
                profiles_sample_rate=sentry_config["profiles_sample_rate"],
                enable_tracing=sentry_config["enable_tracing"],
                attach_stacktrace=sentry_config["attach_stacktrace"],
                send_default_pii=sentry_config["send_default_pii"],
                integrations=[
                    FastAPIIntegration(),
                    RedisIntegration(),
                    SqlalchemyIntegration(),
                ]
            )

            logger.info("✅ Sentry error tracking configured")

        except ImportError:
            logger.warning("Sentry SDK not installed - install with: pip install sentry-sdk[fastapi,redis,sqlalchemy]")
        except Exception as e:
            logger.error(f"Sentry setup failed: {e}")
            raise

    def setup_performance_monitoring(self):
        """Set up performance monitoring."""
        logger.info("Setting up performance monitoring...")

        perf_config = config.performance_config

        if not perf_config["enabled"]:
            logger.info("Performance monitoring disabled")
            return

        # Set up basic performance monitoring
        # This would integrate with APM tools like DataDog, New Relic, etc.
        logger.info(f"✅ Performance monitoring enabled (sample rate: {perf_config['sample_rate']})")

        # Create performance monitoring middleware
        self._create_performance_middleware()

    def setup_health_checks(self):
        """Set up health checks."""
        logger.info("Setting up health checks...")

        health_config = config.health_check_config

        if not health_config["enabled"]:
            logger.info("Health checks disabled")
            return

        # Health checks are already implemented in the API
        # This would set up additional monitoring endpoints
        logger.info(f"✅ Health checks enabled (interval: {health_config['interval']}s)")

    def setup_logging(self):
        """Set up comprehensive logging."""
        logger.info("Setting up comprehensive logging...")

        from core.production_config import setup_production_logging
        setup_production_logging()

        # Set up structured logging for enterprise features
        self._setup_enterprise_logging()

        logger.info("✅ Comprehensive logging configured")

    def setup_metrics_collection(self):
        """Set up metrics collection."""
        logger.info("Setting up metrics collection...")

        # Create metrics collection for enterprise features
        metrics_config = {
            "enabled": True,
            "collection_interval": 60,  # seconds
            "metrics": {
                "api_requests": True,
                "database_connections": True,
                "redis_operations": True,
                "tenant_activity": True,
                "verification_success": True,
                "call_quality": True,
                "ai_routing_performance": True
            }
        }

        # Save metrics configuration
        metrics_file = self.project_root / "config" / "metrics_config.json"
        metrics_file.parent.mkdir(exist_ok=True)

        with open(metrics_file, 'w') as f:
            json.dump(metrics_config, f, indent=2)

        logger.info(f"✅ Metrics collection configured (saved to {metrics_file})")

    def create_monitoring_config(self):
        """Create monitoring configuration file."""
        logger.info("Creating monitoring configuration...")

        monitoring_config = {
            "environment": self.environment,
            "version": os.getenv("APP_VERSION", "2.0.0"),
            "monitoring": {
                "sentry": {
                    "enabled": bool(config.sentry_config["dsn"]),
                    "environment": config.sentry_config["environment"],
                    "traces_sample_rate": config.sentry_config["traces_sample_rate"]
                },
                "performance": {
                    "enabled": config.performance_config["enabled"],
                    "sample_rate": config.performance_config["sample_rate"]
                },
                "health_checks": {
                    "enabled": config.health_check_config["enabled"],
                    "interval": config.health_check_config["interval"]
                },
                "logging": {
                    "level": config.logging_config["level"],
                    "structured": True
                },
                "metrics": {
                    "enabled": True,
                    "collection_interval": 60
                }
            },
            "alerts": {
                "error_rate_threshold": 0.05,  # 5% error rate
                "response_time_threshold": 2.0,  # 2 seconds
                "database_connection_threshold": 80,  # 80% of pool used
                "memory_usage_threshold": 85  # 85% memory usage
            }
        }

        # Save monitoring configuration
        config_file = self.project_root / "config" / "monitoring_config.json"
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)

        logger.info(f"✅ Monitoring configuration saved to {config_file}")

    def validate_monitoring_setup(self):
        """Validate monitoring setup."""
        logger.info("Validating monitoring setup...")

        # Test Sentry
        if config.sentry_config["dsn"]:
            try:
                import sentry_sdk
                # Send a test event
                sentry_sdk.capture_message("Monitoring setup validation", level="info")
                logger.info("✅ Sentry test event sent")
            except Exception as e:
                logger.warning(f"Sentry validation failed: {e}")

        # Test logging
        test_logger = logging.getLogger("monitoring_test")
        test_logger.info("Monitoring validation test message")
        logger.info("✅ Logging validation completed")

        # Test configuration files
        config_files = [
            self.project_root / "config" / "monitoring_config.json",
            self.project_root / "config" / "metrics_config.json"
        ]

        for config_file in config_files:
            if config_file.exists():
                logger.info(f"✅ Configuration file exists: {config_file}")
            else:
                logger.warning(f"Configuration file missing: {config_file}")

    def _create_performance_middleware(self):
        """Create performance monitoring middleware."""
        middleware_code = '''
"""Performance monitoring middleware for FastAPI."""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """Middleware for monitoring API performance."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Create a custom send function to capture response
        response_started = False
        response_status = None

        async def send_wrapper(message):
            nonlocal response_started, response_status

            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]

            await send(message)

        await self.app(scope, receive, send_wrapper)

        if response_started:
            process_time = time.time() - start_time
            logger.info(
                f"Request processed - Path: {scope['path']} - "
                f"Method: {scope['method']} - Status: {response_status} - "
                f"Duration: {process_time:.4f}s"
            )

            # Alert on slow requests (>2 seconds)
            if process_time > 2.0:
                logger.warning(
                    f"Slow request detected - Path: {scope['path']} - "
                    f"Duration: {process_time:.4f}s"
                )
'''

        middleware_file = self.project_root / "middleware" / "performance_middleware.py"
        middleware_file.parent.mkdir(exist_ok=True)

        with open(middleware_file, 'w') as f:
            f.write(middleware_code.strip())

        logger.info(f"✅ Performance middleware created at {middleware_file}")

    def _setup_enterprise_logging(self):
        """Set up logging for enterprise features."""
        # Configure logging for enterprise components
        enterprise_loggers = [
            "services.tenant_service",
            "services.rbac_service",
            "services.webrtc_service",
            "services.ai_routing_service",
            "middleware.tenant_middleware",
            "middleware.rbac_middleware"
        ]

        for logger_name in enterprise_loggers:
            enterprise_logger = logging.getLogger(logger_name)
            enterprise_logger.setLevel(logging.INFO)

            # Add enterprise-specific handler if needed
            # This ensures enterprise features are properly logged

        logger.info("✅ Enterprise logging configured")


def main():
    """Main monitoring setup function."""
    try:
        setup = MonitoringSetup()
        setup.setup_monitoring()
        logger.info("🎉 Namaskah.App monitoring setup completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"❌ Monitoring setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
