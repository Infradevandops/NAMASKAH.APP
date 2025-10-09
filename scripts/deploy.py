#!/usr/bin/env python3
"""
Production deployment script for namaskah.
Handles environment setup, health checks, and deployment verification.
"""
import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages production deployment process."""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.deployment_config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        config_file = self.project_root / f".env.{self.environment}"
        
        if not config_file.exists():
            logger.error(f"Environment file not found: {config_file}")
            sys.exit(1)
            
        config = {}
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
                    
        return config
    
    def validate_environment(self) -> bool:
        """Validate deployment environment."""
        logger.info("🔍 Validating deployment environment...")
        
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL", 
            "SENTRY_DSN"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in self.deployment_config or not self.deployment_config[var]:
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        # Validate secret key strength
        secret_key = self.deployment_config.get("SECRET_KEY", "")
        if len(secret_key) < 32:
            logger.error("❌ SECRET_KEY must be at least 32 characters for production")
            return False
            
        logger.info("✅ Environment validation passed")
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        logger.info("📦 Installing dependencies...")
        
        try:
            # Install Python dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, cwd=self.project_root)
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Setup and migrate database."""
        logger.info("🗄️  Setting up database...")
        
        try:
            # Import here to avoid circular imports
            sys.path.append(str(self.project_root))
            from core.database import check_database_connection, create_tables
            
            # Check database connection
            if not check_database_connection():
                logger.error("❌ Database connection failed")
                return False
            
            # Create/migrate tables
            create_tables()
            logger.info("✅ Database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
    
    def test_sentry_integration(self) -> bool:
        """Test Sentry integration."""
        logger.info("🔧 Testing Sentry integration...")
        
        try:
            import sentry_sdk
            from core.sentry_config import init_sentry
            
            # Initialize Sentry
            init_sentry()
            
            # Send test message
            sentry_sdk.capture_message("Deployment test message", level="info")
            
            logger.info("✅ Sentry integration test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sentry integration test failed: {e}")
            return False
    
    def build_frontend(self) -> bool:
        """Build frontend assets."""
        logger.info("🏗️  Building frontend...")
        
        try:
            frontend_path = self.project_root / "frontend"
            
            if not frontend_path.exists():
                logger.warning("⚠️  Frontend directory not found, skipping build")
                return True
            
            # Install npm dependencies
            subprocess.run(["npm", "install"], check=True, cwd=frontend_path)
            
            # Build production assets
            subprocess.run(["npm", "run", "build"], check=True, cwd=frontend_path)
            
            logger.info("✅ Frontend build completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Frontend build failed: {e}")
            return False
        except FileNotFoundError:
            logger.warning("⚠️  npm not found, skipping frontend build")
            return True
    
    def start_application(self) -> bool:
        """Start the application."""
        logger.info("🚀 Starting application...")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            for key, value in self.deployment_config.items():
                env[key] = value
            
            # Start application in background
            if self.environment == "production":
                # Production: Use gunicorn
                cmd = [
                    "gunicorn",
                    "main:app",
                    "-w", "4",
                    "-k", "uvicorn.workers.UvicornWorker",
                    "--bind", "0.0.0.0:8000",
                    "--access-logfile", "-",
                    "--error-logfile", "-",
                    "--log-level", "info"
                ]
            else:
                # Development: Use uvicorn
                cmd = [
                    "uvicorn",
                    "main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--reload" if self.environment == "development" else "--no-reload"
                ]
            
            # Start process
            self.app_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                env=env
            )
            
            # Wait for application to start
            time.sleep(10)
            
            if self.app_process.poll() is None:
                logger.info("✅ Application started successfully")
                return True
            else:
                logger.error("❌ Application failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start application: {e}")
            return False
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        logger.info("🏥 Running health checks...")
        
        base_url = "http://localhost:8000"
        
        # Wait for application to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{base_url}/health/", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            
            if i == max_retries - 1:
                logger.error("❌ Application not responding to health checks")
                return False
            
            time.sleep(2)
        
        # Run detailed health checks
        health_endpoints = [
            "/health/",
            "/health/detailed",
            "/health/database",
            "/health/system",
            "/health/deployment"
        ]
        
        failed_checks = []
        
        for endpoint in health_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Health check passed: {endpoint}")
                else:
                    logger.error(f"❌ Health check failed: {endpoint} (Status: {response.status_code})")
                    failed_checks.append(endpoint)
                    
            except requests.RequestException as e:
                logger.error(f"❌ Health check error: {endpoint} - {e}")
                failed_checks.append(endpoint)
        
        if failed_checks:
            logger.error(f"❌ Failed health checks: {', '.join(failed_checks)}")
            return False
        
        logger.info("✅ All health checks passed")
        return True
    
    def run_smoke_tests(self) -> bool:
        """Run smoke tests to verify deployment."""
        logger.info("🧪 Running smoke tests...")
        
        base_url = "http://localhost:8000"
        
        test_endpoints = [
            ("/", "GET"),
            ("/api/auth/health", "GET"),
            ("/health/detailed", "GET"),
        ]
        
        failed_tests = []
        
        for endpoint, method in test_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                else:
                    response = requests.request(method, f"{base_url}{endpoint}", timeout=10)
                
                if response.status_code < 500:  # Accept 4xx but not 5xx
                    logger.info(f"✅ Smoke test passed: {method} {endpoint}")
                else:
                    logger.error(f"❌ Smoke test failed: {method} {endpoint} (Status: {response.status_code})")
                    failed_tests.append(f"{method} {endpoint}")
                    
            except requests.RequestException as e:
                logger.error(f"❌ Smoke test error: {method} {endpoint} - {e}")
                failed_tests.append(f"{method} {endpoint}")
        
        if failed_tests:
            logger.error(f"❌ Failed smoke tests: {', '.join(failed_tests)}")
            return False
        
        logger.info("✅ All smoke tests passed")
        return True
    
    def create_deployment_report(self) -> Dict[str, Any]:
        """Create deployment report."""
        return {
            "deployment_id": f"deploy-{int(time.time())}",
            "environment": self.environment,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "version": self.deployment_config.get("APP_VERSION", "1.0.0"),
            "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
            "deployed_by": os.getenv("USER", "unknown"),
            "health_check_url": "http://localhost:8000/health/detailed",
            "sentry_enabled": bool(self.deployment_config.get("SENTRY_DSN")),
            "database_url": self.deployment_config.get("DATABASE_URL", "").split("@")[-1] if "@" in self.deployment_config.get("DATABASE_URL", "") else "local"
        }
    
    def deploy(self) -> bool:
        """Execute full deployment process."""
        logger.info(f"🚀 Starting {self.environment} deployment...")
        
        deployment_steps = [
            ("Environment Validation", self.validate_environment),
            ("Install Dependencies", self.install_dependencies),
            ("Database Setup", self.setup_database),
            ("Sentry Integration Test", self.test_sentry_integration),
            ("Frontend Build", self.build_frontend),
            ("Start Application", self.start_application),
            ("Health Checks", self.run_health_checks),
            ("Smoke Tests", self.run_smoke_tests),
        ]
        
        for step_name, step_func in deployment_steps:
            logger.info(f"📋 Executing: {step_name}")
            
            if not step_func():
                logger.error(f"❌ Deployment failed at step: {step_name}")
                return False
            
            logger.info(f"✅ Completed: {step_name}")
        
        # Create deployment report
        report = self.create_deployment_report()
        
        # Save deployment report
        report_file = self.project_root / f"deployment-report-{report['deployment_id']}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("🎉 Deployment completed successfully!")
        logger.info(f"📊 Deployment report saved: {report_file}")
        logger.info(f"🏥 Health checks: http://localhost:8000/health/detailed")
        logger.info(f"📈 Sentry monitoring: {'Enabled' if report['sentry_enabled'] else 'Disabled'}")
        
        return True
    
    def cleanup(self):
        """Cleanup deployment resources."""
        if hasattr(self, 'app_process') and self.app_process:
            logger.info("🧹 Cleaning up deployment resources...")
            self.app_process.terminate()
            self.app_process.wait()


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy namaskah")
    parser.add_argument(
        "--environment", 
        choices=["development", "production"], 
        default="production",
        help="Deployment environment"
    )
    parser.add_argument(
        "--skip-frontend", 
        action="store_true",
        help="Skip frontend build"
    )
    
    args = parser.parse_args()
    
    # Create deployment manager
    deployment = DeploymentManager(args.environment)
    
    try:
        # Execute deployment
        success = deployment.deploy()
        
        if success:
            logger.info("✅ Deployment successful!")
            sys.exit(0)
        else:
            logger.error("❌ Deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Deployment interrupted by user")
        deployment.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        deployment.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()