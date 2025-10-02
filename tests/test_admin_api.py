#!/usr/bin/env python3
"""
Unit tests for Admin API endpoints
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

# Set test environment
os.environ.update({
    'JWT_SECRET_KEY': 'test_jwt_secret_key_for_testing',
    'USE_MOCK_TWILIO': 'true',
    'DEBUG': 'false'
})


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


class TestAdminAPI:
    """Test admin API endpoints"""

    def test_get_platform_stats(self, client):
        """Test getting platform statistics"""
        response = client.get("/api/admin/stats")

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "verifications" in data
        assert "revenue" in data
        assert "system" in data

        # Check users structure
        users = data["users"]
        assert "total" in users
        assert "active" in users
        assert "new_today" in users

        # Check verifications structure
        verifications = data["verifications"]
        assert "total" in verifications
        assert "today" in verifications
        assert "success_rate" in verifications

    def test_get_users(self, client):
        """Test getting user list"""
        response = client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Check user data structure
        users = data["users"]
        assert isinstance(users, list)
        if users:
            user = users[0]
            assert "id" in user
            assert "email" in user
            assert "username" in user
            assert "credits" in user
            assert "status" in user
            assert "created_at" in user

    def test_get_users_with_params(self, client):
        """Test getting users with limit and offset"""
        response = client.get("/api/admin/users?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_get_verifications(self, client):
        """Test getting verification list"""
        response = client.get("/api/admin/verifications")

        assert response.status_code == 200
        data = response.json()

        assert "verifications" in data
        assert "total" in data
        assert "active" in data
        assert "completed" in data
        assert "failed" in data

        # Check verification data structure
        verifications = data["verifications"]
        assert isinstance(verifications, list)
        if verifications:
            verification = verifications[0]
            assert "id" in verification
            assert "user_id" in verification
            assert "service" in verification
            assert "number" in verification
            assert "status" in verification
            assert "created_at" in verification

    def test_get_verifications_with_status_filter(self, client):
        """Test getting verifications with status filter"""
        response = client.get("/api/admin/verifications?status=completed")

        assert response.status_code == 200
        data = response.json()

        # All returned verifications should have the filtered status
        for verification in data["verifications"]:
            assert verification["status"] == "completed"

    def test_get_revenue_analytics(self, client):
        """Test getting revenue analytics"""
        response = client.get("/api/admin/revenue")

        assert response.status_code == 200
        data = response.json()

        assert "daily" in data
        assert "monthly" in data
        assert "top_services" in data

        # Check daily revenue structure
        daily = data["daily"]
        assert isinstance(daily, list)
        if daily:
            day = daily[0]
            assert "date" in day
            assert "amount" in day

        # Check monthly structure
        monthly = data["monthly"]
        assert "current" in monthly
        assert "previous" in monthly
        assert "growth" in monthly

        # Check top services structure
        top_services = data["top_services"]
        assert isinstance(top_services, list)
        if top_services:
            service = top_services[0]
            assert "service" in service
            assert "revenue" in service
            assert "count" in service

    def test_get_system_health(self, client):
        """Test getting system health status"""
        response = client.get("/api/admin/system/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "services" in data
        assert "metrics" in data

        # Check services structure
        services = data["services"]
        assert "api" in services
        assert "database" in services
        assert "sms_service" in services
        assert "payment_service" in services
        assert "verification_service" in services

        # Check metrics structure
        metrics = data["metrics"]
        assert "uptime" in metrics
        assert "requests_per_minute" in metrics
        assert "error_rate" in metrics
        assert "avg_response_time" in metrics

    def test_suspend_user(self, client):
        """Test suspending a user"""
        user_id = 1
        response = client.post(f"/api/admin/users/{user_id}/suspend")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert f"User {user_id} suspended successfully" in data["message"]

    def test_activate_user(self, client):
        """Test activating a user"""
        user_id = 1
        response = client.post(f"/api/admin/users/{user_id}/activate")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert f"User {user_id} activated successfully" in data["message"]

    def test_toggle_maintenance_mode_enable(self, client):
        """Test enabling maintenance mode"""
        response = client.post("/api/admin/system/maintenance?enabled=true")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Maintenance mode enabled" in data["message"]

    def test_toggle_maintenance_mode_disable(self, client):
        """Test disabling maintenance mode"""
        response = client.post("/api/admin/system/maintenance?enabled=false")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Maintenance mode disabled" in data["message"]

    def test_get_system_logs(self, client):
        """Test getting system logs"""
        response = client.get("/api/admin/logs")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "total" in data

        # Check log data structure
        logs = data["logs"]
        assert isinstance(logs, list)
        if logs:
            log = logs[0]
            assert "timestamp" in log
            assert "level" in log
            assert "message" in log

    def test_get_system_logs_with_filters(self, client):
        """Test getting system logs with level filter"""
        response = client.get("/api/admin/logs?level=info")

        assert response.status_code == 200
        data = response.json()

        # All returned logs should have the filtered level
        for log in data["logs"]:
            assert log["level"] == "info"

    def test_get_system_logs_with_limit(self, client):
        """Test getting system logs with limit"""
        limit = 50
        response = client.get(f"/api/admin/logs?limit={limit}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) <= limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
