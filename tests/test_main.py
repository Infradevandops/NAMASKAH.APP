"""
Tests for main FastAPI application endpoints.
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


def test_test_sentry_endpoint(client):
    """Test the test sentry endpoint."""
    response = client.get("/test-sentry")
    assert response.status_code == 500
    data = response.json()
    assert "Test error for Sentry" in data["detail"]


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "Namaskah.App"
    assert data["version"] == "1.6.0"
    assert "database" in data
    assert "environment" in data
    assert "frontend" in data
    assert "services" in data


def test_detailed_health_endpoint(client):
    """Test the detailed health check endpoint."""
    with patch('psutil.virtual_memory', return_value=MagicMock(percent=50)), \
         patch('psutil.cpu_percent', return_value=20), \
         patch('psutil.disk_usage', return_value=MagicMock(percent=30)):
        
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert data["app_info"]["name"] == "Namaskah.App"
        assert data["app_info"]["version"] == "1.6.0"
        assert "database" in data
        assert "environment" in data
        assert "system" in data
        assert "services" in data
        assert "frontend" in data


def test_home_endpoint_react_build_exists(client):
    """Test the home endpoint when React build exists."""
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open:
        
        mock_file = MagicMock()
        mock_file.read.return_value = "<html>React App</html>"
        mock_open.return_value.__enter__.return_value = mock_file
        
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "React App" in response.text


def test_home_endpoint_no_react_build(client):
    """Test the home endpoint when React build does not exist."""
    with patch('os.path.exists', return_value=False):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Namaskah.App - Development Mode" in response.text


def test_catch_all_route_api(client):
    """Test catch-all route skips API routes."""
    response = client.get("/api/test")
    assert response.status_code == 404


def test_catch_all_route_docs(client):
    """Test catch-all route skips docs."""
    response = client.get("/docs")
    assert response.status_code == 200  # Docs should work


def test_catch_all_route_health(client):
    """Test catch-all route skips health."""
    response = client.get("/health")
    assert response.status_code == 200  # Health should work


def test_catch_all_route_react(client):
    """Test catch-all route serves React for other paths when build exists."""
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open:
        
        mock_file = MagicMock()
        mock_file.read.return_value = "<html>React SPA</html>"
        mock_open.return_value.__enter__.return_value = mock_file
        
        response = client.get("/some/path")
        assert response.status_code == 200
        assert "React SPA" in response.text


def test_openapi_docs(client):
    """Test that OpenAPI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert data["info"]["title"] == "Namaskah.App - Communication Platform"
    assert data["info"]["version"] == "1.6.0"
