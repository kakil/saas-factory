import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.features.users.models import User

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle tenant context
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip tenant context for auth and root endpoints
        if self.is_path_excluded(request.url.path):
            return await call_next(request)

        try:
            # Get tenant ID from request
            tenant_id = await self.get_tenant_id(request)
            if tenant_id:
                # Get database session
                db = next(get_db())
                
                # Set tenant context in database
                db.execute(f"SET app.current_tenant = '{tenant_id}'")
                
                # Store in request state
                request.state.tenant_id = tenant_id
        except Exception as e:
            # Log but don't fail the request if tenant context can't be set
            logger.warning(f"Failed to set tenant context: {str(e)}")
        
        return await call_next(request)
    
    def is_path_excluded(self, path: str) -> bool:
        """
        Check if a path should be excluded from tenant context
        """
        excluded_paths = [
            "/",
            f"{settings.API_V1_STR}/docs",
            f"{settings.API_V1_STR}/redoc",
            f"{settings.API_V1_STR}/openapi.json",
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/auth/",
        ]
        
        return any(path.startswith(excluded) for excluded in excluded_paths)
    
    async def get_tenant_id(self, request: Request) -> Optional[int]:
        """
        Get tenant ID from request
        
        Order of precedence:
        1. X-Tenant-ID header
        2. User's organization_id from authenticated user
        """
        # Check for tenant ID in header
        if "X-Tenant-ID" in request.headers:
            try:
                return int(request.headers["X-Tenant-ID"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid X-Tenant-ID header: {request.headers['X-Tenant-ID']}")
                return None
        
        # Check for authenticated user
        user = getattr(request.state, "user", None)
        if isinstance(user, User) and user.organization_id:
            return user.organization_id
            
        return None