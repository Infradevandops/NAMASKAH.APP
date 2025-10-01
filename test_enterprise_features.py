#!/usr/bin/env python3
"""
Test suite for Phase 3: Enterprise Features
Tests multi-tenant architecture, RBAC, voice/video integration, and advanced AI features
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from main import app
from models.tenant_models import Tenant, TenantUser
from models.rbac_models import Role, Permission, RolePermission, UserRole
from models.call_models import Call, WebRTCSession
from models.routing_models import RoutingRule, RoutingHistory, ConversationIntelligence
from services.tenant_service import TenantService
from services.rbac_service import RBACService
from services.webrtc_service import WebRTCService
from services.ai_routing_service import AIRoutingService
from services.conversation_ai_service import ConversationAIService


class TestEnterpriseFeatures:
    """Test suite for enterprise features"""

    def setup_method(self):
        """Set up test client and database"""
        self.client = TestClient(app)

    def test_tenant_creation(self):
        """Test tenant creation and management"""
        tenant_data = {
            "name": "TestTenant",
            "description": "Test tenant for enterprise features"
        }

        response = self.client.post("/api/tenants", json=tenant_data)
        assert response.status_code == 200
        tenant = response.json()
        assert tenant["name"] == "TestTenant"
        assert tenant["description"] == "Test tenant for enterprise features"

    def test_role_creation(self):
        """Test role creation and permission assignment"""
        role_data = {
            "name": "Admin",
            "description": "Administrator role"
        }

        response = self.client.post("/api/rbac/roles", json=role_data)
        assert response.status_code == 200
        role = response.json()
        assert role["name"] == "Admin"

    def test_permission_creation(self):
        """Test permission creation"""
        permission_data = {
            "name": "manage_users",
            "description": "Can manage users"
        }

        response = self.client.post("/api/rbac/permissions", json=permission_data)
        assert response.status_code == 200
        permission = response.json()
        assert permission["name"] == "manage_users"

    def test_call_initiation(self):
        """Test voice/video call initiation"""
        call_data = {
            "caller_id": "user123",
            "callee_id": "user456",
            "call_type": "video"
        }

        response = self.client.post("/api/calls/initiate", json=call_data)
        assert response.status_code == 200
        call = response.json()
        assert call["call_type"] == "video"
        assert call["status"] == "initiated"

    def test_webrtc_session_management(self):
        """Test WebRTC session creation and management"""
        session_data = {
            "call_id": "call123",
            "offer": "test_offer_sdp"
        }

        response = self.client.post("/api/calls/sessions", json=session_data)
        assert response.status_code == 200
        session = response.json()
        assert session["call_id"] == "call123"

    def test_ai_routing(self):
        """Test AI-based message routing"""
        routing_data = {
            "message_content": "Hello, I need help with my account",
            "sender_id": "user123",
            "context": {
                "sentiment": "neutral",
                "intent": "support"
            }
        }

        response = self.client.post("/api/routing/decide", json=routing_data)
        assert response.status_code == 200
        decision = response.json()
        assert "route" in decision
        assert "confidence_score" in decision

    def test_conversation_intelligence(self):
        """Test conversation analysis and intelligence"""
        conversation_data = {
            "conversation_id": "conv123",
            "messages": [
                {"content": "Hello", "sender": "user"},
                {"content": "Hi there! How can I help?", "sender": "agent"}
            ]
        }

        response = self.client.post("/api/routing/analyze", json=conversation_data)
        assert response.status_code == 200
        analysis = response.json()
        assert "sentiment" in analysis
        assert "keywords" in analysis
        assert "summary" in analysis

    def test_tenant_isolation(self):
        """Test tenant data isolation"""
        # Create two tenants
        tenant1_data = {"name": "Tenant1", "description": "First tenant"}
        tenant2_data = {"name": "Tenant2", "description": "Second tenant"}

        response1 = self.client.post("/api/tenants", json=tenant1_data)
        response2 = self.client.post("/api/tenants", json=tenant2_data)

        tenant1 = response1.json()
        tenant2 = response2.json()

        # Verify tenants are isolated
        assert tenant1["id"] != tenant2["id"]
        assert tenant1["name"] != tenant2["name"]

    def test_rbac_permission_check(self):
        """Test RBAC permission checking"""
        # Create role and permission
        role_response = self.client.post("/api/rbac/roles", json={
            "name": "Manager",
            "description": "Manager role"
        })
        role = role_response.json()

        permission_response = self.client.post("/api/rbac/permissions", json={
            "name": "view_reports",
            "description": "Can view reports"
        })
        permission = permission_response.json()

        # Assign permission to role
        assign_response = self.client.post(
            f"/api/rbac/roles/{role['id']}/permissions/{permission['id']}"
        )
        assert assign_response.status_code == 200

    def test_call_history(self):
        """Test call history and analytics"""
        response = self.client.get("/api/calls/history")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)

    def test_routing_analytics(self):
        """Test routing decision analytics"""
        response = self.client.get("/api/routing/history")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)

    def test_enterprise_health_check(self):
        """Test enterprise features health check"""
        response = self.client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
        assert "tenants" in health
        assert "rbac" in health
        assert "calls" in health
        assert "routing" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
