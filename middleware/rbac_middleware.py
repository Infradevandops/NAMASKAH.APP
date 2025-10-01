import logging
from typing import List, Optional, Union
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from services.rbac_service import RBACService
from models.rbac_models import RBACContext
from models.tenant_models import TenantContext
from core.database import get_db

logger = logging.getLogger(__name__)

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Enhanced RBAC middleware with tenant-aware permission checking
    Sets up RBAC context for each request based on authenticated user and tenant
    """

    def __init__(self, app, rbac_service: RBACService = None):
        super().__init__(app)
        self.rbac_service = rbac_service or RBACService()

    async def dispatch(self, request: Request, call_next):
        try:
            # Extract user and tenant information from request
            user_id = getattr(request.state, 'user_id', None)
            tenant_id = getattr(request.state, 'tenant_id', None)

            if user_id and tenant_id:
                # Set up RBAC context for this request
                self.rbac_service.set_user_permissions_context(tenant_id, user_id)

                logger.debug(f"RBAC context set for user {user_id} in tenant {tenant_id}")
            else:
                # Clear any existing context
                self.rbac_service.clear_permissions_context()
                logger.debug("No user/tenant context available for RBAC")

            response = await call_next(request)

            # Clear RBAC context after request
            self.rbac_service.clear_permissions_context()

            return response

        except Exception as e:
            # Clear context on error
            self.rbac_service.clear_permissions_context()
            logger.error(f"RBAC middleware error: {e}")
            raise


# FastAPI Dependencies for Permission Checking
def require_permission(permission: str, rbac_service: RBACService = Depends(lambda: RBACService())):
    """Dependency that requires a specific permission"""
    if not RBACContext.has_permission(permission):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions: '{permission}' required"
        )
    return True

def require_any_permission(permissions: List[str], rbac_service: RBACService = Depends(lambda: RBACService())):
    """Dependency that requires any of the specified permissions"""
    if not RBACContext.has_any_permission(permissions):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions: one of {permissions} required"
        )
    return True

def require_all_permissions(permissions: List[str], rbac_service: RBACService = Depends(lambda: RBACService())):
    """Dependency that requires all of the specified permissions"""
    if not RBACContext.has_all_permissions(permissions):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions: all of {permissions} required"
        )
    return True

def require_tenant_admin(rbac_service: RBACService = Depends(lambda: RBACService())):
    """Dependency that requires tenant admin role (convenience function)"""
    tenant_id = TenantContext.get_tenant_id()
    user_id = RBACContext.get_current_user_id()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=400, detail="Tenant context not set")

    # Check if user has admin role in tenant
    user_roles = rbac_service.get_user_roles(tenant_id, user_id)
    admin_roles = [role for role in user_roles if role.name in ["admin", "owner"]]

    if not admin_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: tenant admin or owner role required"
        )

    return True

def require_tenant_owner(rbac_service: RBACService = Depends(lambda: RBACService())):
    """Dependency that requires tenant owner role (convenience function)"""
    tenant_id = TenantContext.get_tenant_id()
    user_id = RBACContext.get_current_user_id()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=400, detail="Tenant context not set")

    # Check if user has owner role in tenant
    user_roles = rbac_service.get_user_roles(tenant_id, user_id)
    owner_role = next((role for role in user_roles if role.name == "owner"), None)

    if not owner_role:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: tenant owner role required"
        )

    return True

# Utility functions for permission checking in route handlers
def has_permission(permission: str) -> bool:
    """Check if current user has a specific permission"""
    return RBACContext.has_permission(permission)

def has_any_permission(permissions: List[str]) -> bool:
    """Check if current user has any of the specified permissions"""
    return RBACContext.has_any_permission(permissions)

def has_all_permissions(permissions: List[str]) -> bool:
    """Check if current user has all of the specified permissions"""
    return RBACContext.has_all_permissions(permissions)

def get_current_user_permissions() -> set:
    """Get all permissions for the current user"""
    return RBACContext.get_permissions()

def get_current_user_id() -> Optional[int]:
    """Get the current user ID from RBAC context"""
    return RBACContext.get_current_user_id()

def get_current_tenant_id() -> Optional[int]:
    """Get the current tenant ID from RBAC context"""
    return RBACContext.get_current_tenant_id()

# Permission constants for common operations
class Permissions:
    """Common permission constants"""

    # Tenant permissions
    TENANT_READ = "tenant.read"
    TENANT_UPDATE = "tenant.update"
    TENANT_DELETE = "tenant.delete"

    # User management permissions
    USER_READ = "user.read"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"

    # Role management permissions
    ROLE_READ = "role.read"
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"

    # Verification permissions
    VERIFICATION_READ = "verification.read"
    VERIFICATION_CREATE = "verification.create"
    VERIFICATION_UPDATE = "verification.update"
    VERIFICATION_DELETE = "verification.delete"

    # Communication permissions
    COMMUNICATION_READ = "communication.read"
    COMMUNICATION_CREATE = "communication.create"
    COMMUNICATION_UPDATE = "communication.update"
    COMMUNICATION_DELETE = "communication.delete"

    # Admin permissions (all permissions)
    ADMIN_ALL = [
        TENANT_READ, TENANT_UPDATE, TENANT_DELETE,
        USER_READ, USER_CREATE, USER_UPDATE, USER_DELETE,
        ROLE_READ, ROLE_CREATE, ROLE_UPDATE, ROLE_DELETE, ROLE_ASSIGN,
        VERIFICATION_READ, VERIFICATION_CREATE, VERIFICATION_UPDATE, VERIFICATION_DELETE,
        COMMUNICATION_READ, COMMUNICATION_CREATE, COMMUNICATION_UPDATE, COMMUNICATION_DELETE
    ]

    # Member permissions (basic access)
    MEMBER_BASIC = [
        TENANT_READ,
        USER_READ,
        VERIFICATION_READ, VERIFICATION_CREATE,
        COMMUNICATION_READ, COMMUNICATION_CREATE
    ]
