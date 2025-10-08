#!/usr/bin/env python3
"""
Comprehensive API test suite covering all major endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and system endpoints"""

    def test_health_check(self, client: TestClient):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "app_name" in data
        assert data["app_name"] == "Namaskah.App"

    def test_detailed_health_check(self, client: TestClient):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "environment" in data
        assert "services" in data


class TestAuthenticationAPI:
    """Test authentication endpoints"""

    def test_user_registration(self, client: TestClient, test_user_data):
        """Test user registration"""
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user_data["email"]

    def test_user_login(self, client: TestClient, test_user_data):
        """Test user login"""
        # First register
        client.post("/api/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user profile"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data


class TestVerificationAPI:
    """Test SMS verification endpoints"""

    def test_create_verification(self, client: TestClient, mock_verification_data):
        """Test creating verification session"""
        response = client.post("/api/verification/create", json=mock_verification_data)
        assert response.status_code == 200
        data = response.json()
        assert "verification_id" in data
        assert "status" in data

    def test_get_verification_number(self, client: TestClient, mock_verification_data):
        """Test getting verification phone number"""
        # Create verification first
        create_response = client.post("/api/verification/create", json=mock_verification_data)
        verification_id = create_response.json()["verification_id"]
        
        # Get number
        response = client.get(f"/api/verification/{verification_id}/number")
        assert response.status_code == 200
        data = response.json()
        assert "phone_number" in data

    def test_get_verification_messages(self, client: TestClient, mock_verification_data):
        """Test getting verification messages"""
        # Create verification first
        create_response = client.post("/api/verification/create", json=mock_verification_data)
        verification_id = create_response.json()["verification_id"]
        
        # Get messages
        response = client.get(f"/api/verification/{verification_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data


class TestCommunicationAPI:
    """Test communication endpoints"""

    def test_create_conversation(self, client: TestClient, auth_headers, mock_conversation_data):
        """Test creating a conversation"""
        response = client.post("/api/conversations", json=mock_conversation_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "title" in data

    def test_send_message(self, client: TestClient, auth_headers, mock_message_data):
        """Test sending a message"""
        # Create conversation first
        conv_data = {"title": "Test Conversation"}
        conv_response = client.post("/api/conversations", json=conv_data, headers=auth_headers)
        conversation_id = conv_response.json()["id"]
        
        # Send message
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json=mock_message_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "content" in data


class TestAIAssistantAPI:
    """Test AI assistant endpoints"""

    def test_ai_chat(self, client: TestClient):
        """Test AI chat endpoint"""
        chat_data = {
            "message": "Hello, how can you help me?",
            "context": "general_inquiry"
        }
        response = client.post("/api/ai/chat", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_analyze_intent(self, client: TestClient):
        """Test message intent analysis"""
        response = client.post("/api/ai/analyze-intent", params={"message": "I need help with verification"})
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "sentiment" in data


class TestPerformanceAPI:
    """Test performance monitoring endpoints"""

    def test_get_metrics(self, client: TestClient, admin_headers):
        """Test getting system metrics"""
        response = client.get("/api/performance/metrics", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "database" in data

    def test_get_usage_stats(self, client: TestClient, admin_headers):
        """Test getting usage statistics"""
        response = client.get("/api/performance/usage", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data or "message" in data  # May be empty initially


@pytest.mark.integration
class TestEndToEndFlows:
    """Test complete user flows"""

    def test_complete_verification_flow(self, client: TestClient):
        """Test complete SMS verification flow"""
        # 1. Create verification
        verification_data = {"service_name": "whatsapp", "capability": "sms"}
        create_response = client.post("/api/verification/create", json=verification_data)
        assert create_response.status_code == 200
        verification_id = create_response.json()["verification_id"]
        
        # 2. Get phone number
        number_response = client.get(f"/api/verification/{verification_id}/number")
        assert number_response.status_code == 200
        
        # 3. Check messages
        messages_response = client.get(f"/api/verification/{verification_id}/messages")
        assert messages_response.status_code == 200
        
        # 4. Check status
        status_response = client.get(f"/api/verification/{verification_id}/status")
        assert status_response.status_code == 200

    def test_complete_user_journey(self, client: TestClient, test_user_data):
        """Test complete user registration and usage flow"""
        # 1. Register user
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get user profile
        profile_response = client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        # 3. Create conversation
        conv_data = {"title": "My First Conversation"}
        conv_response = client.post("/api/conversations", json=conv_data, headers=headers)
        assert conv_response.status_code == 201
        conversation_id = conv_response.json()["id"]
        
        # 4. Send message
        message_data = {"content": "Hello world!", "message_type": "text"}
        message_response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json=message_data,
            headers=headers
        )
        assert message_response.status_code == 201


@pytest.mark.performance
class TestPerformanceRequirements:
    """Test performance requirements"""

    def test_health_check_response_time(self, client: TestClient):
        """Test health check responds within 1 second"""
        import time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_api_documentation_loads(self, client: TestClient):
        """Test API documentation loads successfully"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


@pytest.mark.security
class TestSecurityRequirements:
    """Test security requirements"""

    def test_protected_endpoints_require_auth(self, client: TestClient):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/api/auth/me",
            "/api/conversations",
            "/api/performance/metrics"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_invalid_token_rejected(self, client: TestClient):
        """Test that invalid tokens are rejected"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=invalid_headers)
        assert response.status_code == 401

    def test_sql_injection_protection(self, client: TestClient):
        """Test SQL injection protection"""
        malicious_data = {
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "password123"
        }
        response = client.post("/api/auth/login", json=malicious_data)
        # Should not crash the server
        assert response.status_code in [400, 401, 422]  # Bad request or validation error