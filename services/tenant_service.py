import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.tenant_models import (
    Tenant, TenantUser, TenantSettings, TenantInvitation, TenantContext
)
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class TenantService:
    """Enhanced tenant service with comprehensive multi-tenant management"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_tenant(self, name: str, description: str = None, domain: str = None,
                     created_by_user_id: int = None) -> Tenant:
        """Create a new tenant with default settings"""
        try:
            # Create tenant
            tenant = Tenant(
                name=name,
                description=description,
                domain=domain
            )
            self.db.add(tenant)
            self.db.flush()  # Get tenant ID without committing

            # Create default settings
            settings = TenantSettings(tenant_id=tenant.id)
            self.db.add(settings)

            # Add creator as owner if provided
            if created_by_user_id:
                owner_user = TenantUser(
                    tenant_id=tenant.id,
                    user_id=created_by_user_id,
                    role="owner",
                    joined_at=datetime.utcnow()
                )
                self.db.add(owner_user)

            self.db.commit()
            self.db.refresh(tenant)
            logger.info(f"Created tenant: {tenant.name} (ID: {tenant.id})")
            return tenant

        except IntegrityError as e:
            self.db.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError(f"Tenant with name '{name}' or domain '{domain}' already exists")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create tenant: {e}")
            raise

    def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.db.query(Tenant).filter(
            Tenant.id == tenant_id,
            Tenant.is_active == True
        ).first()

    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        return self.db.query(Tenant).filter(
            Tenant.domain == domain,
            Tenant.is_active == True
        ).first()

    def update_tenant(self, tenant_id: int, **updates) -> Optional[Tenant]:
        """Update tenant information"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def deactivate_tenant(self, tenant_id: int) -> bool:
        """Deactivate a tenant (soft delete)"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.is_active = False
        self.db.commit()
        logger.info(f"Deactivated tenant: {tenant.name} (ID: {tenant.id})")
        return True

    # User Management
    def add_user_to_tenant(self, tenant_id: int, user_id: int, role: str = "member",
                          invited_by_user_id: int = None) -> TenantUser:
        """Add a user to a tenant"""
        try:
            tenant_user = TenantUser(
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.utcnow()
            )
            self.db.add(tenant_user)
            self.db.commit()
            self.db.refresh(tenant_user)
            logger.info(f"Added user {user_id} to tenant {tenant_id} with role {role}")
            return tenant_user
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"User {user_id} is already a member of tenant {tenant_id}")

    def update_user_role(self, tenant_id: int, user_id: int, new_role: str) -> bool:
        """Update a user's role in a tenant"""
        tenant_user = self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id
        ).first()

        if not tenant_user:
            return False

        tenant_user.role = new_role
        self.db.commit()
        return True

    def remove_user_from_tenant(self, tenant_id: int, user_id: int) -> bool:
        """Remove a user from a tenant"""
        tenant_user = self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id
        ).first()

        if not tenant_user:
            return False

        self.db.delete(tenant_user)
        self.db.commit()
        logger.info(f"Removed user {user_id} from tenant {tenant_id}")
        return True

    def get_tenant_users(self, tenant_id: int) -> List[TenantUser]:
        """Get all users in a tenant"""
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.is_active == True
        ).all()

    def get_user_tenants(self, user_id: int) -> List[Tenant]:
        """Get all tenants a user belongs to"""
        tenant_users = self.db.query(TenantUser).filter(
            TenantUser.user_id == user_id,
            TenantUser.is_active == True
        ).all()

        tenant_ids = [tu.tenant_id for tu in tenant_users]
        return self.db.query(Tenant).filter(
            Tenant.id.in_(tenant_ids),
            Tenant.is_active == True
        ).all()

    # Invitation Management
    def create_invitation(self, tenant_id: int, email: str, role: str,
                         invited_by_user_id: int, expires_days: int = 7) -> TenantInvitation:
        """Create a tenant invitation"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            invited_by_user_id=invited_by_user_id,
            token=token,
            expires_at=expires_at
        )

        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def accept_invitation(self, token: str, user_id: int) -> bool:
        """Accept a tenant invitation"""
        invitation = self.db.query(TenantInvitation).filter(
            TenantInvitation.token == token,
            TenantInvitation.expires_at > datetime.utcnow(),
            TenantInvitation.accepted_at.is_(None)
        ).first()

        if not invitation:
            return False

        # Add user to tenant
        self.add_user_to_tenant(
            invitation.tenant_id,
            user_id,
            invitation.role
        )

        # Mark invitation as accepted
        invitation.accepted_at = datetime.utcnow()
        self.db.commit()

        return True

    # Settings Management
    def get_tenant_settings(self, tenant_id: int) -> Optional[TenantSettings]:
        """Get tenant settings"""
        return self.db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()

    def update_tenant_settings(self, tenant_id: int, **updates) -> bool:
        """Update tenant settings"""
        settings = self.get_tenant_settings(tenant_id)
        if not settings:
            return False

        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        self.db.commit()
        return True

    # Context Management
    def set_tenant_context(self, tenant_id: int):
        """Set the current tenant context for this request"""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            TenantContext.set_tenant(tenant_id, tenant)
            return True
        return False

    def get_current_tenant(self) -> Optional[Tenant]:
        """Get the current tenant from context"""
        return TenantContext.get_tenant()

    def get_current_tenant_id(self) -> Optional[int]:
        """Get the current tenant ID from context"""
        return TenantContext.get_tenant_id()

    def clear_tenant_context(self):
        """Clear the tenant context"""
        TenantContext.clear()

    # Utility Methods
    def validate_tenant_access(self, user_id: int, tenant_id: int) -> bool:
        """Check if a user has access to a tenant"""
        tenant_user = self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id,
            TenantUser.is_active == True
        ).first()
        return tenant_user is not None

    def get_user_role_in_tenant(self, user_id: int, tenant_id: int) -> Optional[str]:
        """Get a user's role in a specific tenant"""
        tenant_user = self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id,
            TenantUser.is_active == True
        ).first()
        return tenant_user.role if tenant_user else None

    def is_tenant_owner(self, user_id: int, tenant_id: int) -> bool:
        """Check if a user is the owner of a tenant"""
        return self.get_user_role_in_tenant(user_id, tenant_id) == "owner"

    def is_tenant_admin(self, user_id: int, tenant_id: int) -> bool:
        """Check if a user is an admin or owner of a tenant"""
        role = self.get_user_role_in_tenant(user_id, tenant_id)
        return role in ["owner", "admin"]
