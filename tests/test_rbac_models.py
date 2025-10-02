#!/usr/bin/env python3
"""
Unit tests for RBAC models
"""
import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.rbac_models import (
    Role,
    Permission,
    RolePermission,
    UserRole,
    PermissionAuditLog,
    RBACContext,
)
from models.user_models import User
from models.tenant_models import Tenant
from core.database import Base


@pytest.fixture(scope="module")
def test_engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestRoleModel:
    """Test cases for Role model"""

    def test_role_creation(self, db_session):
        """Test creating a role"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        role = Role(
            tenant_id=tenant.id,
            name="admin",
            description="Administrator role",
            is_system_role=True,
            is_active=True
        )
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.tenant_id == tenant.id
        assert role.name == "admin"
        assert role.is_system_role is True

    def test_role_repr(self, db_session):
        """Test string representation of role"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        role = Role(
            tenant_id=tenant.id,
            name="user",
            description="Regular user role"
        )
        expected = f"<Role(id={role.id}, tenant_id={tenant.id}, name='user')>"
        assert repr(role) == expected


class TestPermissionModel:
    """Test cases for Permission model"""

    def test_permission_creation(self, db_session):
        """Test creating a permission"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        permission = Permission(
            tenant_id=tenant.id,
            name="user.create",
            resource="user",
            action="create",
            description="Create users",
            is_system_permission=True
        )
        db_session.add(permission)
        db_session.commit()

        assert permission.id is not None
        assert permission.name == "user.create"
        assert permission.resource == "user"
        assert permission.action == "create"

    def test_permission_repr(self, db_session):
        """Test string representation of permission"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        permission = Permission(
            tenant_id=tenant.id,
            name="user.read",
            resource="user",
            action="read"
        )
        expected = f"<Permission(id={permission.id}, tenant_id={tenant.id}, name='user.read')>"
        assert repr(permission) == expected


class TestRolePermissionModel:
    """Test cases for RolePermission model"""

    def test_role_permission_creation(self, db_session):
        """Test creating a role-permission association"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        user = User(
            email="admin@test.com",
            username="admin",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        role = Role(
            tenant_id=tenant.id,
            name="admin",
            description="Administrator role"
        )
        db_session.add(role)
        db_session.commit()

        permission = Permission(
            tenant_id=tenant.id,
            name="user.manage",
            resource="user",
            action="manage"
        )
        db_session.add(permission)
        db_session.commit()

        role_perm = RolePermission(
            tenant_id=tenant.id,
            role_id=role.id,
            permission_id=permission.id,
            granted_by_user_id=user.id
        )
        db_session.add(role_perm)
        db_session.commit()

        assert role_perm.id is not None
        assert role_perm.role_id == role.id
        assert role_perm.permission_id == permission.id

    def test_role_permission_repr(self, db_session):
        """Test string representation of role permission"""
        role_perm = RolePermission(
            tenant_id=1,
            role_id=1,
            permission_id=1,
            granted_by_user_id=1
        )
        expected = "<RolePermission(role_id=1, permission_id=1)>"
        assert repr(role_perm) == expected


class TestUserRoleModel:
    """Test cases for UserRole model"""

    def test_user_role_creation(self, db_session):
        """Test creating a user-role assignment"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        user = User(
            email="user@test.com",
            username="testuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        admin = User(
            email="admin@test.com",
            username="admin",
            hashed_password="pass"
        )
        db_session.add(admin)
        db_session.commit()

        role = Role(
            tenant_id=tenant.id,
            name="user",
            description="Regular user role"
        )
        db_session.add(role)
        db_session.commit()

        user_role = UserRole(
            tenant_id=tenant.id,
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=admin.id,
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )
        db_session.add(user_role)
        db_session.commit()

        assert user_role.id is not None
        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.is_active is True

    def test_user_role_repr(self, db_session):
        """Test string representation of user role"""
        user_role = UserRole(
            tenant_id=1,
            user_id=1,
            role_id=1,
            assigned_by_user_id=1
        )
        expected = "<UserRole(tenant_id=1, user_id=1, role_id=1)>"
        assert repr(user_role) == expected


class TestPermissionAuditLogModel:
    """Test cases for PermissionAuditLog model"""

    def test_audit_log_creation(self, db_session):
        """Test creating an audit log entry"""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.com",
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()

        user = User(
            email="auditor@test.com",
            username="auditor",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        audit_log = PermissionAuditLog(
            tenant_id=tenant.id,
            user_id=user.id,
            action="create",
            resource_type="role",
            resource_id=1,
            old_values=None,
            new_values='{"name": "new_role"}',
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0..."
        )
        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.id is not None
        assert audit_log.action == "create"
        assert audit_log.resource_type == "role"

    def test_audit_log_repr(self, db_session):
        """Test string representation of audit log"""
        audit_log = PermissionAuditLog(
            tenant_id=1,
            user_id=1,
            action="update",
            resource_type="permission",
            resource_id=1
        )
        expected = "<PermissionAuditLog(tenant_id=1, action='update', resource_type='permission')>"
        assert repr(audit_log) == expected


class TestRBACContext:
    """Test cases for RBACContext utility class"""

    def test_rbac_context_operations(self):
        """Test RBAC context permission management"""
        # Clear context first
        RBACContext.clear()

        # Test setting permissions
        permissions = {"user.create", "user.read", "role.manage"}
        RBACContext.set_permissions(permissions, user_id=1, tenant_id=1)

        assert RBACContext.get_permissions() == permissions
        assert RBACContext.get_current_user_id() == 1
        assert RBACContext.get_current_tenant_id() == 1

        # Test permission checks
        assert RBACContext.has_permission("user.create") is True
        assert RBACContext.has_permission("admin.delete") is False

        # Test multiple permission checks
        assert RBACContext.has_any_permission(["user.create", "admin.delete"]) is True
        assert RBACContext.has_all_permissions(["user.create", "user.read"]) is True
        assert RBACContext.has_all_permissions(["user.create", "admin.delete"]) is False

        # Test clearing
        RBACContext.clear()
        assert RBACContext.get_permissions() == set()
        assert RBACContext.get_current_user_id() is None
        assert RBACContext.get_current_tenant_id() is None


if __name__ == "__main__":
    pytest.main([__file__])
