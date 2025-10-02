#!/usr/bin/env python3
"""
Unit tests for Admin API endpoints with database and auth
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.jwt_handler import create_jwt_token
from core.database import Base, get_db
from main import app
from models.user_models import SubscriptionPlan, User

# Set test environment
os.environ.update({
    'JWT_SECRET_KEY': 'test_jwt_secret_key_for_testing',
    'USE_MOCK_TWILIO': 'true',
    'DEBUG': 'false'
})

# Test database setup
@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        subscription_plan=SubscriptionPlan.BASIC,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with JWT token"""
    token = create_jwt_token({"user_id": test_user.id, "email": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_session):
    """Create test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestAdminAPI:
    """Test admin API endpoints"""

    def test_get_platform_stats(self, client, auth_headers):
        """Test getting platform statistics"""
        response = client.get("/api/admin/stats", headers=auth_headers)

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

    def test_get_users(self, client, auth_headers):
        """Test getting user list"""
        response = client.get("/api/admin/users", headers=auth_headers)

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

    def test_get_users_with_params(self, client, auth_headers):
        """Test getting users with limit and offset"""
        response = client.get("/api/admin/users?limit=10&offset=0", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_get_verifications(self, client, auth_headers):
        """Test getting verification list"""
        response = client.get("/api/admin/verifications", headers=auth_headers)

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

    def test_get_verifications_with_status_filter(self, client, auth_headers):
        """Test getting verifications with status filter"""
        response = client.get("/api/admin/verifications?status=completed", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # All returned verifications should have the filtered status
        for verification in data["verifications"]:
            assert verification["status"] == "completed"

    def test_get_revenue_analytics(self, client, auth_headers):
        """Test getting revenue analytics"""
        response = client.get("/api/admin/revenue", headers=auth_headers)

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

    def test_get_system_health(self, client, auth_headers):
        """Test getting system health status"""
        response = client.get("/api/admin/system/health", headers=auth_headers)

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

    def test_suspend_user(self, client, auth_headers):
        """Test suspending a user"""
        user_id = 1
        response = client.post(f"/api/admin/users/{user_id}/suspend", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert f"User {user_id} suspended successfully" in data["message"]

    def test_activate_user(self, client, auth_headers):
        """Test activating a user"""
        user_id = 1
        response = client.post(f"/api/admin/users/{user_id}/activate", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert f"User {user_id} activated successfully" in data["message"]

    def test_toggle_maintenance_mode_enable(self, client, auth_headers):
        """Test enabling maintenance mode"""
        response = client.post("/api/admin/system/maintenance?enabled=true", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Maintenance mode enabled" in data["message"]

    def test_toggle_maintenance_mode_disable(self, client, auth_headers):
        """Test disabling maintenance mode"""
        response = client.post("/api/admin/system/maintenance?enabled=false", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Maintenance mode disabled" in data["message"]

    def test_get_system_logs(self, client, auth_headers):
        """Test getting system logs"""
        response = client.get("/api/admin/logs", headers=auth_headers)

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

    def test_get_system_logs_with_filters(self, client, auth_headers):
        """Test getting system logs with level filter"""
        response = client.get("/api/admin/logs?level=info", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # All returned logs should have the filtered level
        for log in data["logs"]:
            assert log["level"] == "info"

    def test_get_system_logs_with_limit(self, client, auth_headers):
        """Test getting system logs with limit"""
        limit = 50
        response = client.get(f"/api/admin/logs?limit={limit}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) <= limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
