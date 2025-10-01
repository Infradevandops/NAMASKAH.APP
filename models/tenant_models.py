from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String, unique=True, index=True, nullable=True)  # For subdomain routing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    settings = relationship("TenantSettings", back_populates="tenant", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', domain='{self.domain}')>"

class TenantUser(Base):
    __tablename__ = "tenant_users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False, default="member")  # member, admin, owner
    is_active = Column(Boolean, default=True, nullable=False)
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    joined_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        {"schema": None},  # Will be set dynamically for multi-tenant isolation
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    user = relationship("User")

    def __repr__(self):
        return f"<TenantUser(tenant_id={self.tenant_id}, user_id={self.user_id}, role='{self.role}')>"

class TenantSettings(Base):
    __tablename__ = "tenant_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)

    # Feature flags
    enable_verification = Column(Boolean, default=True, nullable=False)
    enable_voice_calls = Column(Boolean, default=False, nullable=False)
    enable_video_calls = Column(Boolean, default=False, nullable=False)
    enable_ai_routing = Column(Boolean, default=False, nullable=False)

    # Limits and quotas
    max_users = Column(Integer, default=10, nullable=False)
    max_monthly_messages = Column(Integer, default=1000, nullable=False)
    max_concurrent_calls = Column(Integer, default=1, nullable=False)

    # Branding
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, default="#3b82f6", nullable=False)
    company_name = Column(String, nullable=True)

    # Security settings
    require_mfa = Column(Boolean, default=False, nullable=False)
    session_timeout_hours = Column(Integer, default=24, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="settings")

    def __repr__(self):
        return f"<TenantSettings(tenant_id={self.tenant_id}, max_users={self.max_users})>"

class TenantInvitation(Base):
    __tablename__ = "tenant_invitations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(String, default="member", nullable=False)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    invited_by = relationship("User")

    def __repr__(self):
        return f"<TenantInvitation(tenant_id={self.tenant_id}, email='{self.email}', role='{self.role}')>"

# Tenant context for request-scoped tenant information
class TenantContext:
    """Thread-local storage for current tenant context"""
    _current_tenant_id = None
    _current_tenant = None

    @classmethod
    def set_tenant(cls, tenant_id: int, tenant=None):
        """Set the current tenant for this request context"""
        cls._current_tenant_id = tenant_id
        cls._current_tenant = tenant

    @classmethod
    def get_tenant_id(cls) -> int:
        """Get the current tenant ID"""
        return cls._current_tenant_id

    @classmethod
    def get_tenant(cls):
        """Get the current tenant object"""
        return cls._current_tenant

    @classmethod
    def clear(cls):
        """Clear the tenant context"""
        cls._current_tenant_id = None
        cls._current_tenant = None
