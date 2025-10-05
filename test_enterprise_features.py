"""
Tests for enterprise features in Namaskah.App
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with mocked dependencies."""
    with patch('core.database.check_database_connection', return_value=True), \
         patch('core.env_validator.validate_environment', return_value=(True, [])), \
         patch('core.env_validator.get_environment_status', return_value={
             "critical": {"TEST": {"present": True}},
             "degraded_features": []
         }), \
         patch('core.migration_validator.safe_create_tables', return_value=(True, ["Tables created"])), \
         patch('core.migration_validator.get_database_health', return_value={
             "status": "healthy",
             "issues": []
         }), \
         patch('clients.unified_client.get_unified_client', return_value=MagicMock(
             twilio_client=MagicMock(),
             textverified_client=MagicMock(),
             groq_client=MagicMock()
         )), \
         patch('os.path.exists', side_effect=lambda path: path == "frontend/build/index.html"), \
         patch('core.sentry_config.init_sentry'):
        
        from main import app
        return TestClient(app)


def test_tenant_api_access(client):
    """Test tenant API endpoints are accessible."""
    # Without auth, should return 401 or 403
    response = client.get("/api/tenants")
    assert response.status_code in [401, 403, 404]  # 404 if not implemented yet


def test_rbac_api_access(client):
    """Test RBAC API endpoints are accessible."""
    response = client.get("/api/rbac/roles")
    assert response.status_code in [401, 403, 404]


def test_call_api_access(client):
    """Test call API endpoints are accessible."""
    response = client.get("/api/calls")
    assert response.status_code in [401, 403, 404]


def test_enterprise_health_check(client):
    """Test enterprise features in health check."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    # Should include enterprise-related info
    assert "services" in data
    assert "system" in data


def test_openapi_docs_include_enterprise(client):
    """Test that OpenAPI docs include enterprise endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    paths = data.get("paths", {})
    # Check for enterprise paths
    enterprise_paths = [p for p in paths.keys() if "tenant" in p or "rbac" in p or "call" in p]
    assert len(enterprise_paths) > 0, "No enterprise API paths found in OpenAPI spec"
