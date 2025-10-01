from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)  # Built-in roles that can't be deleted
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_tenant_role_name'),
    )

    # Relationships
    tenant = relationship("Tenant", backref="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}')>"

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)  # e.g., "tenant.create", "user.manage"
    resource = Column(String, nullable=False, index=True)  # e.g., "tenant", "user", "verification"
    action = Column(String, nullable=False)  # e.g., "create", "read", "update", "delete", "manage"
    description = Column(Text, nullable=True)
    is_system_permission = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_tenant_permission_name'),
    )

    # Relationships
    tenant = relationship("Tenant", backref="permissions")
    roles = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permission(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}')>"

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    granted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'role_id', 'permission_id', name='uq_tenant_role_permission'),
    )

    # Relationships
    tenant = relationship("Tenant", backref="role_permissions")
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")
    granted_by = relationship("User")

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For temporary role assignments
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'role_id', name='uq_tenant_user_role'),
    )

    # Relationships
    tenant = relationship("Tenant", backref="user_roles")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])

    def __repr__(self):
        return f"<UserRole(tenant_id={self.tenant_id}, user_id={self.user_id}, role_id={self.role_id})>"

class PermissionAuditLog(Base):
    """Audit log for permission changes"""
    __tablename__ = "permission_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who made the change
    action = Column(String, nullable=False)  # create, update, delete
    resource_type = Column(String, nullable=False)  # role, permission, user_role
    resource_id = Column(Integer, nullable=False)  # ID of the affected resource
    old_values = Column(Text, nullable=True)  # JSON of old values
    new_values = Column(Text, nullable=True)  # JSON of new values
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", backref="permission_audit_logs")
    user = relationship("User")

    def __repr__(self):
        return f"<PermissionAuditLog(tenant_id={self.tenant_id}, action='{self.action}', resource_type='{self.resource_type}')>"

# RBAC Context for request-scoped RBAC information
class RBACContext:
    """Thread-local storage for current user's permissions"""
    _current_permissions = set()
    _current_user_id = None
    _current_tenant_id = None

    @classmethod
    def set_permissions(cls, permissions: set, user_id: int = None, tenant_id: int = None):
        """Set the current user's permissions for this request context"""
        cls._current_permissions = permissions or set()
        cls._current_user_id = user_id
        cls._current_tenant_id = tenant_id

    @classmethod
    def get_permissions(cls) -> set:
        """Get the current user's permissions"""
        return cls._current_permissions

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        """Check if current user has a specific permission"""
        return permission in cls._current_permissions

    @classmethod
    def has_any_permission(cls, permissions: list) -> bool:
        """Check if current user has any of the specified permissions"""
        return bool(cls._current_permissions.intersection(set(permissions)))

    @classmethod
    def has_all_permissions(cls, permissions: list) -> bool:
        """Check if current user has all of the specified permissions"""
        return set(permissions).issubset(cls._current_permissions)

    @classmethod
    def get_current_user_id(cls) -> int:
        """Get the current user ID"""
        return cls._current_user_id

    @classmethod
    def get_current_tenant_id(cls) -> int:
        """Get the current tenant ID"""
        return cls._current_tenant_id

    @classmethod
    def clear(cls):
        """Clear the RBAC context"""
        cls._current_permissions = set()
        cls._current_user_id = None
        cls._current_tenant_id = None
