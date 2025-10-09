#!/usr/bin/env python3
"""
Setup script for performance monitoring with Sentry.
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_sentry_dsn():
    """Check if Sentry DSN is configured."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("SENTRY_DSN environment variable not set")
        logger.info("To enable Sentry monitoring, set SENTRY_DSN in your environment:")
        logger.info("export SENTRY_DSN='https://your-dsn@sentry.io/project-id'")
        return False
    return True


def install_dependencies():
    """Install Sentry SDK and other performance monitoring dependencies."""
    try:
        logger.info("Installing performance monitoring dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False


def test_sentry_integration():
    """Test Sentry integration."""
    try:
        logger.info("Testing Sentry integration...")

        # Import and initialize Sentry
        try:
            from core.sentry_config import init_sentry
            init_sentry()
        except ImportError:
            logger.warning("⚠️  Could not import core modules, skipping Sentry test")
            return True

        # Test error capture
        import sentry_sdk
        sentry_sdk.capture_message("Test message from performance monitoring setup", level="info")

        logger.info("✅ Sentry integration test completed")
        return True
    except Exception as e:
        logger.error(f"❌ Sentry integration test failed: {e}")
        return False


def test_performance_service():
    """Test performance service functionality."""
    try:
        logger.info("Testing performance service...")

        try:
            from services.performance_service import performance_service

            # Test tracking metrics
            performance_service.track_core_web_vital("lcp", 2500, {"page": "test"})
            performance_service.track_api_performance("/api/test", 0.5, 200, "GET")
            performance_service.track_chat_performance("message_processing", 1.2, 1)

            # Test summary generation
            summary = performance_service.get_performance_summary()
            logger.info(f"Performance summary generated: {len(summary)} categories")

            # Test budget checking
            budgets = performance_service.check_performance_budgets()
            logger.info(f"Budget violations: {sum(budgets.values())}")

            logger.info("✅ Performance service test completed")
            return True
        except ImportError:
            logger.warning("⚠️  Could not import services modules, skipping performance service test")
            return True
    except Exception as e:
        logger.error(f"❌ Performance service test failed: {e}")
        return False


def create_sample_env_file():
    """Create a sample .env file with performance monitoring configuration."""
    env_content = """# Performance Monitoring Configuration
# Copy this file to .env and configure your actual values

# Sentry Configuration (Required for error tracking and performance monitoring)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
ENVIRONMENT=development

# Performance Budgets (Optional - these are defaults)
PERFORMANCE_API_BUDGET=1.0
PERFORMANCE_DB_BUDGET=0.5
PERFORMANCE_CHAT_BUDGET=2.0

# Core Web Vitals Budgets (Optional - these are defaults)
LCP_BUDGET=2500
FID_BUDGET=100
CLS_BUDGET=0.1
"""

    try:
        with open(".env.performance.example", "w") as f:
            f.write(env_content)
        logger.info("✅ Sample environment file created: .env.performance.example")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create sample env file: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("🚀 Setting up Performance Monitoring for namaskah")
    logger.info("=" * 50)

    success_count = 0
    total_checks = 5

    # Check 1: Install dependencies
    if install_dependencies():
        success_count += 1

    # Check 2: Check Sentry DSN
    sentry_configured = check_sentry_dsn()

    # Check 3: Test Sentry integration (only if DSN is configured)
    if sentry_configured and test_sentry_integration():
        success_count += 1

    # Check 4: Test performance service
    if test_performance_service():
        success_count += 1

    # Check 5: Create sample env file
    if create_sample_env_file():
        success_count += 1

    logger.info("=" * 50)
    logger.info(f"Setup completed: {success_count}/{total_checks} checks passed")

    if success_count == total_checks:
        logger.info("🎉 Performance monitoring setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Configure your SENTRY_DSN in .env file")
        logger.info("2. Access the performance dashboard at: http://localhost:8000/performance")
        logger.info("3. Check performance metrics at: http://localhost:8000/api/performance/metrics")
        logger.info("4. Monitor errors and performance in your Sentry dashboard")
    else:
        logger.warning("⚠️  Some setup steps failed. Please check the errors above.")
        logger.info("\nTroubleshooting:")
        logger.info("- Ensure all dependencies are installed")
        logger.info("- Configure SENTRY_DSN environment variable")
        logger.info("- Check logs for detailed error messages")

    return success_count == total_checks


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)