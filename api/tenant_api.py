from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.database import get_db
from services.tenant_service import TenantService
from middleware.tenant_middleware import (
    get_current_tenant_id,
    require_tenant_admin,
    require_tenant_owner
)

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Pydantic models
class TenantCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    domain: Optional[str] = None

class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None

class TenantSettingsUpdateRequest(BaseModel):
    enable_verification: Optional[bool] = None
    enable_voice_calls: Optional[bool] = None
    enable_video_calls: Optional[bool] = None
    enable_ai_routing: Optional[bool] = None
    max_users: Optional[int] = None
    max_monthly_messages: Optional[int] = None
    max_concurrent_calls: Optional[int] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    company_name: Optional[str] = None
    require_mfa: Optional[bool] = None
    session_timeout_hours: Optional[int] = None

class TenantInvitationRequest(BaseModel):
    email: EmailStr
    role: str = "member"
    expires_days: int = 7

class AddUserRequest(BaseModel):
    user_id: int
    role: str = "member"

class UpdateUserRoleRequest(BaseModel):
    role: str

# Dependencies
def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)

# Tenant CRUD endpoints
@router.post("/", response_model=dict)
def create_tenant(
    request: TenantCreateRequest,
    created_by_user_id: int,  # This would come from auth in real implementation
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant"""
    try:
        tenant = tenant_service.create_tenant(
            name=request.name,
            description=request.description,
            domain=request.domain,
            created_by_user_id=created_by_user_id
        )
        return {
            "id": tenant.id,
            "name": tenant.name,
            "description": tenant.description,
            "domain": tenant.domain,
            "created_at": tenant.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tenant_id}")
def get_tenant(
    tenant_id: int,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by ID"""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "domain": tenant.domain,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at
    }

@router.put("/{tenant_id}")
def update_tenant(
    tenant_id: int,
    request: TenantUpdateRequest,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant information"""
    # Check permissions (owner only)
    require_tenant_owner(user_id, tenant_service)

    tenant = tenant_service.update_tenant(tenant_id, **request.dict(exclude_unset=True))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "domain": tenant.domain,
        "is_active": tenant.is_active,
        "updated_at": tenant.updated_at
    }

@router.delete("/{tenant_id}")
def deactivate_tenant(
    tenant_id: int,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Deactivate a tenant (soft delete)"""
    # Check permissions (owner only)
    require_tenant_owner(user_id, tenant_service)

    success = tenant_service.deactivate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"message": "Tenant deactivated successfully"}

# User management endpoints
@router.post("/{tenant_id}/users")
def add_user_to_tenant(
    tenant_id: int,
    request: AddUserRequest,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Add a user to a tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(user_id, tenant_service)

    try:
        tenant_user = tenant_service.add_user_to_tenant(
            tenant_id=tenant_id,
            user_id=request.user_id,
            role=request.role
        )
        return {
            "tenant_id": tenant_user.tenant_id,
            "user_id": tenant_user.user_id,
            "role": tenant_user.role,
            "joined_at": tenant_user.joined_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tenant_id}/users/{target_user_id}/role")
def update_user_role(
    tenant_id: int,
    target_user_id: int,
    request: UpdateUserRoleRequest,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update a user's role in a tenant"""
    # Check permissions (admin or owner, and not updating themselves to lower role)
    require_tenant_admin(user_id, tenant_service)

    # Prevent users from demoting themselves
    if user_id == target_user_id and request.role not in ["owner", "admin"]:
        current_role = tenant_service.get_user_role_in_tenant(user_id, tenant_id)
        if current_role in ["owner", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Cannot demote your own admin/owner role"
            )

    success = tenant_service.update_user_role(tenant_id, target_user_id, request.role)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in tenant")

    return {"message": "User role updated successfully"}

@router.delete("/{tenant_id}/users/{target_user_id}")
def remove_user_from_tenant(
    tenant_id: int,
    target_user_id: int,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Remove a user from a tenant"""
    # Check permissions (admin or owner, and not removing themselves)
    require_tenant_admin(user_id, tenant_service)

    # Prevent users from removing themselves
    if user_id == target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot remove yourself from tenant"
        )

    success = tenant_service.remove_user_from_tenant(tenant_id, target_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in tenant")

    return {"message": "User removed from tenant successfully"}

@router.get("/{tenant_id}/users")
def get_tenant_users(
    tenant_id: int,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get all users in a tenant"""
    # Check permissions (member or higher)
    if not tenant_service.validate_tenant_access(user_id, tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    users = tenant_service.get_tenant_users(tenant_id)
    return [
        {
            "user_id": tu.user_id,
            "role": tu.role,
            "is_active": tu.is_active,
            "joined_at": tu.joined_at,
            "user": {
                "id": tu.user.id,
                "email": tu.user.email,
                "first_name": tu.user.first_name,
                "last_name": tu.user.last_name
            } if tu.user else None
        }
        for tu in users
    ]

# Settings management endpoints
@router.get("/{tenant_id}/settings")
def get_tenant_settings(
    tenant_id: int,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get tenant settings"""
    # Check permissions (member or higher)
    if not tenant_service.validate_tenant_access(user_id, tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    settings = tenant_service.get_tenant_settings(tenant_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Tenant settings not found")

    return {
        "tenant_id": settings.tenant_id,
        "enable_verification": settings.enable_verification,
        "enable_voice_calls": settings.enable_voice_calls,
        "enable_video_calls": settings.enable_video_calls,
        "enable_ai_routing": settings.enable_ai_routing,
        "max_users": settings.max_users,
        "max_monthly_messages": settings.max_monthly_messages,
        "max_concurrent_calls": settings.max_concurrent_calls,
        "logo_url": settings.logo_url,
        "primary_color": settings.primary_color,
        "company_name": settings.company_name,
        "require_mfa": settings.require_mfa,
        "session_timeout_hours": settings.session_timeout_hours,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at
    }

@router.put("/{tenant_id}/settings")
def update_tenant_settings(
    tenant_id: int,
    request: TenantSettingsUpdateRequest,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant settings"""
    # Check permissions (admin or owner)
    require_tenant_admin(user_id, tenant_service)

    success = tenant_service.update_tenant_settings(
        tenant_id,
        **request.dict(exclude_unset=True)
    )

    if not success:
        raise HTTPException(status_code=404, detail="Tenant settings not found")

    return {"message": "Tenant settings updated successfully"}

# Invitation management endpoints
@router.post("/{tenant_id}/invitations")
def create_invitation(
    tenant_id: int,
    request: TenantInvitationRequest,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a tenant invitation"""
    # Check permissions (admin or owner)
    require_tenant_admin(user_id, tenant_service)

    invitation = tenant_service.create_invitation(
        tenant_id=tenant_id,
        email=request.email,
        role=request.role,
        invited_by_user_id=user_id,
        expires_days=request.expires_days
    )

    return {
        "id": invitation.id,
        "tenant_id": invitation.tenant_id,
        "email": invitation.email,
        "role": invitation.role,
        "token": invitation.token,
        "expires_at": invitation.expires_at,
        "created_at": invitation.created_at
    }

@router.post("/invitations/{token}/accept")
def accept_invitation(
    token: str,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Accept a tenant invitation"""
    success = tenant_service.accept_invitation(token, user_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invitation token"
        )

    return {"message": "Invitation accepted successfully"}

# User-specific endpoints
@router.get("/user/{user_id}")
def get_user_tenants(
    user_id: int,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get all tenants a user belongs to"""
    tenants = tenant_service.get_user_tenants(user_id)
    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "description": tenant.description,
            "domain": tenant.domain,
            "role": tenant_service.get_user_role_in_tenant(user_id, tenant.id)
        }
        for tenant in tenants
    ]

# Utility endpoints
@router.get("/{tenant_id}/validate-access/{target_user_id}")
def validate_tenant_access(
    tenant_id: int,
    target_user_id: int,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Check if a user has access to a tenant"""
    has_access = tenant_service.validate_tenant_access(target_user_id, tenant_id)
    return {"has_access": has_access}

@router.get("/{tenant_id}/user/{target_user_id}/role")
def get_user_role_in_tenant(
    tenant_id: int,
    target_user_id: int,
    user_id: int,  # This would come from auth
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get a user's role in a tenant"""
    # Check permissions (member or higher)
    if not tenant_service.validate_tenant_access(user_id, tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    role = tenant_service.get_user_role_in_tenant(target_user_id, tenant_id)
    return {"role": role}
