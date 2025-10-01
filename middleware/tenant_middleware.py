import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from services.tenant_service import TenantService
from models.tenant_models import TenantContext

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Enhanced tenant middleware with multiple tenant identification methods
    Supports: X-Tenant-ID header, subdomain routing, and JWT token claims
    """

    def __init__(self, app, tenant_service: TenantService = None):
        super().__init__(app)
        self.tenant_service = tenant_service or TenantService()

    async def dispatch(self, request: Request, call_next):
        try:
            # Extract tenant identifier from multiple sources
            tenant_id = await self._extract_tenant_id(request)

            if tenant_id:
                # Set tenant context for this request
                success = self.tenant_service.set_tenant_context(tenant_id)
                if success:
                    # Add tenant info to request state for backward compatibility
                    tenant = self.tenant_service.get_current_tenant()
                    request.state.tenant = tenant
                    request.state.tenant_id = tenant_id

                    logger.debug(f"Tenant context set: {tenant.name if tenant else 'Unknown'} (ID: {tenant_id})")
                else:
                    logger.warning(f"Failed to set tenant context for ID: {tenant_id}")
            else:
                # For public endpoints that don't require tenant context
                logger.debug("No tenant context required for this request")

            response = await call_next(request)

            # Clear tenant context after request
            self.tenant_service.clear_tenant_context()

            return response

        except Exception as e:
            # Clear context on error
            self.tenant_service.clear_tenant_context()
            logger.error(f"Tenant middleware error: {e}")
            raise

    async def _extract_tenant_id(self, request: Request) -> Optional[int]:
        """
        Extract tenant ID from multiple sources in order of priority:
        1. X-Tenant-ID header
        2. Subdomain routing
        3. JWT token claims (future implementation)
        4. Query parameter (fallback)
        """

        # 1. Check X-Tenant-ID header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            try:
                return int(tenant_header)
            except ValueError:
                logger.warning(f"Invalid X-Tenant-ID header: {tenant_header}")

        # 2. Check subdomain routing
        tenant_id = self._extract_tenant_from_subdomain(request)
        if tenant_id:
            return tenant_id

        # 3. Check JWT token claims (placeholder for future auth integration)
        # This would be implemented when JWT authentication is added
        # tenant_id = self._extract_tenant_from_jwt(request)
        # if tenant_id:
        #     return tenant_id

        # 4. Check query parameter (fallback for development/testing)
        tenant_param = request.query_params.get("tenant_id")
        if tenant_param:
            try:
                return int(tenant_param)
            except ValueError:
                logger.warning(f"Invalid tenant_id query parameter: {tenant_param}")

        return None

    def _extract_tenant_from_subdomain(self, request: Request) -> Optional[int]:
        """
        Extract tenant ID from subdomain
        Format: {tenant-domain}.cumapp.com -> lookup tenant by domain
        """
        try:
            host = request.headers.get("host", "").lower()

            # Remove port if present
            if ":" in host:
                host = host.split(":")[0]

            # Skip if it's an IP address
            if host.replace(".", "").isdigit():
                return None

            # Extract subdomain (assuming format: subdomain.domain.com)
            parts = host.split(".")
            if len(parts) >= 3:  # subdomain.domain.tld
                subdomain = parts[0]

                # Skip common subdomains
                if subdomain in ["www", "api", "app", "dev", "staging", "test"]:
                    return None

                # Look up tenant by domain
                tenant = self.tenant_service.get_tenant_by_domain(subdomain)
                return tenant.id if tenant else None

        except Exception as e:
            logger.warning(f"Error extracting tenant from subdomain: {e}")

        return None

    def _extract_tenant_from_jwt(self, request: Request) -> Optional[int]:
        """
        Extract tenant ID from JWT token claims
        Placeholder for future JWT authentication integration
        """
        # TODO: Implement when JWT authentication is added
        # This would extract tenant_id from JWT token claims
        return None


# Dependency for FastAPI routes that require tenant context
def get_current_tenant():
    """Dependency to get current tenant"""
    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context not set")
    return tenant

def get_current_tenant_id():
    """Dependency to get current tenant ID"""
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context not set")
    return tenant_id

def require_tenant_admin(user_id: int, tenant_service: TenantService = Depends(lambda: TenantService())):
    """Dependency that requires tenant admin or owner role"""
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context not set")

    if not tenant_service.is_tenant_admin(user_id, tenant_id):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: tenant admin or owner role required"
        )

    return True

def require_tenant_owner(user_id: int, tenant_service: TenantService = Depends(lambda: TenantService())):
    """Dependency that requires tenant owner role"""
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context not set")

    if not tenant_service.is_tenant_owner(user_id, tenant_id):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: tenant owner role required"
        )

    return True
