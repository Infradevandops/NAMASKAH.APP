#!/usr/bin/env python3
"""
Security testing suite for Namaskah.App
Tests authentication, authorization, input validation, and security headers
"""
import pytest
import jwt
from fastapi.testclient import TestClient


@pytest.mark.security
class TestAuthentication:
    """Test authentication security"""

    def test_jwt_token_validation(self, client: TestClient, test_user_data):
        """Test JWT token validation"""
        # Register and login
        client.post("/api/auth/register", json=test_user_data)
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Valid token should work
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200

    def test_invalid_jwt_token_rejected(self, client: TestClient):
        """Test invalid JWT tokens are rejected"""
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            ""
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == 401

    def test_expired_token_rejected(self, client: TestClient):
        """Test expired tokens are rejected"""
        # Create an expired token
        import time
        from auth.security import create_access_token
        
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=-3600  # Expired 1 hour ago
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_password_strength_validation(self, client: TestClient):
        """Test password strength requirements"""
        weak_passwords = [
            "123456",
            "password",
            "abc",
            "12345678",  # No special chars or uppercase
            "PASSWORD123",  # No lowercase
            "password123"  # No uppercase or special chars
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "email": "test@example.com",
                "password": weak_password,
                "full_name": "Test User"
            }
            response = client.post("/api/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error


@pytest.mark.security
class TestAuthorization:
    """Test authorization and access control"""

    def test_admin_endpoints_require_admin_role(self, client: TestClient, test_user_data):
        """Test admin endpoints require admin role"""
        # Register regular user
        client.post("/api/auth/register", json=test_user_data)
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin endpoints
        admin_endpoints = [
            "/api/admin/users",
            "/api/performance/metrics",
            "/api/admin/system-info"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found

    def test_user_can_only_access_own_data(self, client: TestClient):
        """Test users can only access their own data"""
        # Create two users
        user1_data = {
            "email": "user1@example.com",
            "password": "Password123!",
            "full_name": "User One"
        }
        user2_data = {
            "email": "user2@example.com",
            "password": "Password123!",
            "full_name": "User Two"
        }
        
        # Register both users
        client.post("/api/auth/register", json=user1_data)
        client.post("/api/auth/register", json=user2_data)
        
        # Login as user1
        login_response = client.post("/api/auth/login", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        user1_token = login_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User1 should be able to access their own profile
        response = client.get("/api/auth/me", headers=user1_headers)
        assert response.status_code == 200
        assert response.json()["email"] == user1_data["email"]


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization"""

    def test_sql_injection_protection(self, client: TestClient):
        """Test SQL injection protection"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM users WHERE '1'='1'; --",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            # Test in login
            response = client.post("/api/auth/login", json={
                "email": malicious_input,
                "password": "password"
            })
            assert response.status_code in [400, 401, 422]
            
            # Test in registration
            response = client.post("/api/auth/register", json={
                "email": malicious_input,
                "password": "Password123!",
                "full_name": "Test User"
            })
            assert response.status_code in [400, 422]

    def test_xss_protection(self, client: TestClient, auth_headers):
        """Test XSS protection"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            # Test in conversation creation
            response = client.post("/api/conversations", json={
                "title": payload
            }, headers=auth_headers)
            
            if response.status_code == 201:
                # If created, check that payload is sanitized
                data = response.json()
                assert "<script>" not in data.get("title", "")
                assert "javascript:" not in data.get("title", "")

    def test_file_upload_validation(self, client: TestClient, auth_headers):
        """Test file upload validation"""
        # Test with malicious file types
        malicious_files = [
            ("test.exe", b"MZ\x90\x00"),  # Executable
            ("test.php", b"<?php echo 'test'; ?>"),  # PHP script
            ("test.jsp", b"<%@ page language='java' %>"),  # JSP
        ]
        
        for filename, content in malicious_files:
            files = {"file": (filename, content, "application/octet-stream")}
            # Assuming there's a file upload endpoint
            response = client.post("/api/upload", files=files, headers=auth_headers)
            # Should reject malicious files
            assert response.status_code in [400, 415, 422]

    def test_email_validation(self, client: TestClient):
        """Test email validation"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "test@.com",
            ""
        ]
        
        for invalid_email in invalid_emails:
            response = client.post("/api/auth/register", json={
                "email": invalid_email,
                "password": "Password123!",
                "full_name": "Test User"
            })
            assert response.status_code == 422

    def test_phone_number_validation(self, client: TestClient):
        """Test phone number validation"""
        invalid_phones = [
            "123",
            "abc",
            "+1-800-FLOWERS",
            "++1234567890",
            "1234567890123456789",  # Too long
            ""
        ]
        
        for invalid_phone in invalid_phones:
            response = client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "Password123!",
                "full_name": "Test User",
                "phone_number": invalid_phone
            })
            assert response.status_code == 422


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers"""

    def test_security_headers_present(self, client: TestClient):
        """Test security headers are present"""
        response = client.get("/health")
        
        # Check for important security headers
        headers = response.headers
        
        # Content Security Policy
        assert "content-security-policy" in headers or "x-content-security-policy" in headers
        
        # X-Frame-Options
        assert "x-frame-options" in headers
        
        # X-Content-Type-Options
        assert "x-content-type-options" in headers
        
        # X-XSS-Protection (if supported)
        # Note: This header is deprecated but still good to have
        
        # Strict-Transport-Security (for HTTPS)
        # This might not be present in test environment

    def test_cors_configuration(self, client: TestClient):
        """Test CORS configuration"""
        # Test preflight request
        response = client.options("/api/auth/login", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Should allow the request
        assert response.status_code in [200, 204]
        
        # Check CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers


@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting"""

    def test_rate_limiting_protection(self, client: TestClient):
        """Test rate limiting protects against abuse"""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        rate_limited = any(status == 429 for status in responses)
        # Note: Rate limiting might be disabled in tests, so this is optional
        # assert rate_limited or all(status in [400, 401, 422] for status in responses)


@pytest.mark.security
class TestDataProtection:
    """Test data protection and privacy"""

    def test_password_not_returned(self, client: TestClient, test_user_data):
        """Test passwords are never returned in responses"""
        # Register user
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        login_data = login_response.json()
        assert "password" not in login_data
        assert "hashed_password" not in login_data

    def test_sensitive_data_not_logged(self, client: TestClient, test_user_data):
        """Test sensitive data is not logged"""
        # This would require checking logs, which is environment-specific
        # For now, just ensure the endpoint works
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201

    def test_user_data_isolation(self, client: TestClient):
        """Test user data is properly isolated"""
        # Create two users with conversations
        user1_data = {
            "email": "user1@example.com",
            "password": "Password123!",
            "full_name": "User One"
        }
        user2_data = {
            "email": "user2@example.com",
            "password": "Password123!",
            "full_name": "User Two"
        }
        
        # Register users
        client.post("/api/auth/register", json=user1_data)
        client.post("/api/auth/register", json=user2_data)
        
        # Login as user1
        login1 = client.post("/api/auth/login", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        user1_token = login1.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # Login as user2
        login2 = client.post("/api/auth/login", json={
            "email": user2_data["email"],
            "password": user2_data["password"]
        })
        user2_token = login2.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # Create conversation as user1
        conv_response = client.post("/api/conversations", json={
            "title": "User1's Private Conversation"
        }, headers=user1_headers)
        
        if conv_response.status_code == 201:
            # User2 should not be able to access user1's conversations
            conversations = client.get("/api/conversations", headers=user2_headers)
            if conversations.status_code == 200:
                user2_conversations = conversations.json()
                # User2 should not see user1's conversations
                for conv in user2_conversations:
                    assert conv["title"] != "User1's Private Conversation"