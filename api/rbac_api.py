from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.database import get_db
from services.rbac_service import RBACService
from middleware.tenant_middleware import get_current_tenant_id
from middleware.rbac_middleware import (
    require_permission,
    require_tenant_admin,
    Permissions
)

router = APIRouter(prefix="/rbac", tags=["rbac"])

# Pydantic models
class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionCreateRequest(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None

class AssignPermissionRequest(BaseModel):
    permission_id: int

class AssignRoleRequest(BaseModel):
    role_id: int
    expires_at: Optional[datetime] = None

class UpdateUserRoleRequest(BaseModel):
    role_id: int
    expires_at: Optional[datetime] = None

# Dependencies
def get_rbac_service(db: Session = Depends(get_db)) -> RBACService:
    return RBACService(db)

# Role Management Endpoints
@router.post("/roles", response_model=dict)
def create_role(
    request: RoleCreateRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Create a new role in the current tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    try:
        role = rbac_service.create_role(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            created_by_user_id=user_id
        )
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "created_at": role.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/roles")
def get_tenant_roles(
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all active roles in the current tenant"""
    # Check permissions (member or higher)
    require_permission(Permissions.ROLE_READ)

    roles = rbac_service.get_tenant_roles(tenant_id)
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "is_active": role.is_active,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
        for role in roles
    ]

@router.get("/roles/{role_id}")
def get_role(
    role_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get a specific role by ID"""
    # Check permissions (member or higher)
    require_permission(Permissions.ROLE_READ)

    role = rbac_service.get_role(tenant_id, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "is_active": role.is_active,
        "created_at": role.created_at,
        "updated_at": role.updated_at
    }

@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Update a role"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    role = rbac_service.update_role(
        tenant_id=tenant_id,
        role_id=role_id,
        name=request.name,
        description=request.description,
        updated_by_user_id=user_id
    )

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "updated_at": role.updated_at
    }

@router.delete("/roles/{role_id}")
def deactivate_role(
    role_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Deactivate a role (soft delete)"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    success = rbac_service.deactivate_role(
        tenant_id=tenant_id,
        role_id=role_id,
        deactivated_by_user_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Role not found")

    return {"message": "Role deactivated successfully"}

# Permission Management Endpoints
@router.post("/permissions", response_model=dict)
def create_permission(
    request: PermissionCreateRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Create a new permission in the current tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    try:
        permission = rbac_service.create_permission(
            tenant_id=tenant_id,
            name=request.name,
            resource=request.resource,
            action=request.action,
            description=request.description,
            created_by_user_id=user_id
        )
        return {
            "id": permission.id,
            "name": permission.name,
            "resource": permission.resource,
            "action": permission.action,
            "description": permission.description,
            "is_system_permission": permission.is_system_permission,
            "created_at": permission.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/permissions")
def get_tenant_permissions(
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions in the current tenant"""
    # Check permissions (member or higher)
    require_permission(Permissions.ROLE_READ)

    permissions = rbac_service.get_tenant_permissions(tenant_id)
    return [
        {
            "id": perm.id,
            "name": perm.name,
            "resource": perm.resource,
            "action": perm.action,
            "description": perm.description,
            "is_system_permission": perm.is_system_permission,
            "created_at": perm.created_at
        }
        for perm in permissions
    ]

# Role-Permission Assignment Endpoints
@router.post("/roles/{role_id}/permissions")
def assign_permission_to_role(
    role_id: int,
    request: AssignPermissionRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Assign a permission to a role"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    try:
        role_permission = rbac_service.assign_permission_to_role(
            tenant_id=tenant_id,
            role_id=role_id,
            permission_id=request.permission_id,
            assigned_by_user_id=user_id
        )
        return {
            "role_id": role_permission.role_id,
            "permission_id": role_permission.permission_id,
            "granted_at": role_permission.granted_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/roles/{role_id}/permissions/{permission_id}")
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Remove a permission from a role"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    success = rbac_service.remove_permission_from_role(
        tenant_id=tenant_id,
        role_id=role_id,
        permission_id=permission_id,
        removed_by_user_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Role-permission assignment not found")

    return {"message": "Permission removed from role successfully"}

@router.get("/roles/{role_id}/permissions")
def get_role_permissions(
    role_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions assigned to a role"""
    # Check permissions (member or higher)
    require_permission(Permissions.ROLE_READ)

    permissions = rbac_service.get_role_permissions(tenant_id, role_id)
    return [
        {
            "id": perm.id,
            "name": perm.name,
            "resource": perm.resource,
            "action": perm.action,
            "description": perm.description
        }
        for perm in permissions
    ]

# User-Role Assignment Endpoints
@router.post("/users/{target_user_id}/roles")
def assign_role_to_user(
    target_user_id: int,
    request: AssignRoleRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Assign a role to a user in the current tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    try:
        user_role = rbac_service.assign_role_to_user(
            tenant_id=tenant_id,
            user_id=target_user_id,
            role_id=request.role_id,
            assigned_by_user_id=user_id,
            expires_at=request.expires_at
        )
        return {
            "user_id": user_role.user_id,
            "role_id": user_role.role_id,
            "assigned_at": user_role.assigned_at,
            "expires_at": user_role.expires_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{target_user_id}/roles/{role_id}")
def update_user_role(
    target_user_id: int,
    role_id: int,
    request: UpdateUserRoleRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Update a user's role assignment (for changing expiration, etc.)"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    # For now, this is a placeholder - the service method would need to be updated
    # to support updating existing assignments
    raise HTTPException(status_code=501, detail="Role update not implemented yet")

@router.delete("/users/{target_user_id}/roles/{role_id}")
def remove_role_from_user(
    target_user_id: int,
    role_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Remove a role from a user in the current tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    success = rbac_service.remove_role_from_user(
        tenant_id=tenant_id,
        user_id=target_user_id,
        role_id=role_id,
        removed_by_user_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="User-role assignment not found")

    return {"message": "Role removed from user successfully"}

@router.get("/users/{target_user_id}/roles")
def get_user_roles(
    target_user_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all roles assigned to a user in the current tenant"""
    # Check permissions (member or higher, or viewing own roles)
    user_id = user_id  # This would come from auth middleware
    if target_user_id != user_id:
        require_permission(Permissions.USER_READ)

    roles = rbac_service.get_user_roles(tenant_id, target_user_id)
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role
        }
        for role in roles
    ]

@router.get("/roles/{role_id}/users")
def get_users_with_role(
    role_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all users with a specific role in the current tenant"""
    # Check permissions (admin or owner)
    require_tenant_admin(rbac_service)

    user_roles = rbac_service.get_users_with_role(tenant_id, role_id)
    return [
        {
            "user_id": ur.user_id,
            "assigned_at": ur.assigned_at,
            "expires_at": ur.expires_at,
            "is_active": ur.is_active,
            "user": {
                "id": ur.user.id,
                "email": ur.user.email,
                "first_name": ur.user.first_name,
                "last_name": ur.user.last_name
            } if ur.user else None
        }
        for ur in user_roles
    ]

# Permission Checking Endpoints
@router.get("/users/{target_user_id}/permissions")
def get_user_permissions(
    target_user_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for a user in the current tenant"""
    # Check permissions (member or higher, or checking own permissions)
    user_id = user_id  # This would come from auth middleware
    if target_user_id != user_id:
        require_permission(Permissions.USER_READ)

    permissions = rbac_service.get_user_permissions(tenant_id, target_user_id)
    return {"permissions": list(permissions)}

@router.get("/check/{permission_name}")
def check_current_user_permission(
    permission_name: str,
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if current user has a specific permission"""
    has_perm = rbac_service.check_user_permission(tenant_id, user_id, permission_name)
    return {"has_permission": has_perm}

@router.post("/check-multiple")
def check_current_user_permissions(
    permission_names: List[str],
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if current user has any of the specified permissions"""
    has_perms = rbac_service.check_user_permissions(tenant_id, user_id, permission_names)
    return {"has_permissions": has_perms}

# Utility Endpoints
@router.get("/current/permissions")
def get_current_user_permissions_endpoint(
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for the current user"""
    permissions = rbac_service.get_user_permissions(tenant_id, user_id)
    return {"permissions": list(permissions)}

@router.get("/current/context")
def get_current_rbac_context(
    tenant_id: int = Depends(get_current_tenant_id),
    user_id: int = Depends(lambda: None),  # This would come from auth middleware
):
    """Get current RBAC context information"""
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "permissions": list(Permissions.MEMBER_BASIC)  # This would be dynamic based on actual permissions
    }
