#!/usr/bin/env python3
"""
Enterprise feature tests for Namaskah.App
Tests multi-tenant, RBAC, and enterprise-specific functionality
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set test environment
os.environ.update({
    'JWT_SECRET_KEY': 'test_jwt_secret_key_for_testing_enterprise_features',
    'USE_MOCK_TWILIO': 'true',
    'USE_MOCK_TEXTVERIFIED': 'true',
    'DEBUG': 'false',
    'ENVIRONMENT': 'testing'
})

from main import app

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


class TestEnterpriseFeatures:
    """Test enterprise-specific features"""

    def test_health_endpoint(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "app_name" in data
        assert data["app_name"] == "Namaskah.App"

    def test_detailed_health_endpoint(self, client):
        """Test detailed health endpoint"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "database" in data
        assert "services" in data

    def test_api_documentation(self, client):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    def test_tenant_endpoints_require_auth(self, client):
        """Test that tenant endpoints require authentication"""
        response = client.get("/api/tenants")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_rbac_endpoints_require_auth(self, client):
        """Test that RBAC endpoints require authentication"""
        response = client.get("/api/rbac/roles")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_call_endpoints_require_auth(self, client):
        """Test that call endpoints require authentication"""
        response = client.get("/api/calls")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_admin_endpoints_require_auth(self, client):
        """Test that admin endpoints require authentication"""
        response = client.get("/api/admin/stats")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_environment_validation(self, client):
        """Test environment validation through health check"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        # Should have environment status
        assert "environment" in data
        env_data = data["environment"]
        assert "critical" in env_data
        assert "optional" in env_data

    def test_database_health(self, client):
        """Test database health monitoring"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        # Should have database status
        assert "database" in data
        db_data = data["database"]
        assert "connection" in db_data

    def test_service_availability(self, client):
        """Test service availability reporting"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        # Should have services status
        assert "services" in data
        services = data["services"]
        assert "twilio" in services
        assert "textverified" in services
        assert "groq" in services

    def test_system_monitoring(self, client):
        """Test system resource monitoring"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        # Should have system information
        assert "system" in data or "timestamp" in data

    def test_graceful_degradation(self, client):
        """Test that missing services don't crash the app"""
        # App should start and respond even with missing API keys
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should show degraded status or warnings, not crash
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])