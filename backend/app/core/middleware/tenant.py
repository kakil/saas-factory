import logging
from typing import Optional, List, Dict, Any

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.features.users.models import User
from app.features.teams.models import Organization

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware for multi-tenant context management
    
    This middleware handles setting the tenant context for each request by:
    1. Extracting tenant ID from request headers or authenticated user
    2. Setting appropriate database session variables for row-level security
    3. Storing tenant information in request state for use by handlers
    
    The middleware integrates with PostgreSQL's Row-Level Security features
    by setting the app.current_tenant parameter which is used by RLS policies.
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._excluded_paths = self._get_excluded_paths()
        self._tenant_cache: Dict[int, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process each request to set tenant context"""
        # Skip tenant context for excluded endpoints
        if self.is_path_excluded(request.url.path):
            # Clear tenant context for excluded paths to ensure no leakage
            await self._clear_tenant_context(request)
            return await call_next(request)

        try:
            # Get tenant ID from request
            tenant_id = await self.get_tenant_id(request)
            
            if tenant_id:
                # Set tenant context
                await self._set_tenant_context(request, tenant_id)
                
                # Get tenant info and cache it
                tenant_info = await self._get_tenant_info(request, tenant_id)
                request.state.tenant_info = tenant_info
            else:
                # Clear tenant context if no tenant ID found
                await self._clear_tenant_context(request)
                
        except Exception as e:
            # Log but don't fail the request if tenant context can't be set
            logger.warning(f"Failed to set tenant context: {str(e)}")
            await self._clear_tenant_context(request)
        
        # Process the request with tenant context set
        response = await call_next(request)
        
        # Clean up after request (ensure no tenant context leaks between requests)
        await self._cleanup_tenant_context(request)
        
        return response
    
    async def _set_tenant_context(self, request: Request, tenant_id: int) -> None:
        """Set tenant context in database and request state"""
        try:
            # Get database session
            db = next(get_db())
            
            # Set tenant context in database session
            db.execute(f"SET app.current_tenant = '{tenant_id}'")
            
            # Store in request state for easy access by handlers
            request.state.tenant_id = tenant_id
            
            logger.debug(f"Set tenant context to {tenant_id}")
        except SQLAlchemyError as e:
            logger.error(f"Database error setting tenant context: {str(e)}")
            raise
    
    async def _clear_tenant_context(self, request: Request) -> None:
        """Clear tenant context from database and request state"""
        try:
            # Get database session
            db = next(get_db())
            
            # Clear tenant context in database
            db.execute("SET app.current_tenant = NULL")
            
            # Clear request state
            if hasattr(request.state, "tenant_id"):
                delattr(request.state, "tenant_id")
            if hasattr(request.state, "tenant_info"):
                delattr(request.state, "tenant_info")
                
            logger.debug("Cleared tenant context")
        except SQLAlchemyError as e:
            logger.error(f"Database error clearing tenant context: {str(e)}")
    
    async def _cleanup_tenant_context(self, request: Request) -> None:
        """Cleanup after request to prevent context leakage"""
        try:
            # Clear tenant context from database session
            # This is a safety measure to ensure no tenant context leaks between requests
            db = next(get_db())
            db.execute("SET app.current_tenant = NULL")
        except Exception as e:
            logger.debug(f"Error during tenant context cleanup: {str(e)}")
    
    async def _get_tenant_info(self, request: Request, tenant_id: int) -> Dict[str, Any]:
        """Get tenant information and cache it"""
        # Check cache first
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]
        
        try:
            # Get database session
            db = next(get_db())
            
            # Get organization info
            org = db.query(Organization).filter(Organization.id == tenant_id).first()
            
            if not org:
                logger.warning(f"Tenant not found: {tenant_id}")
                return {"id": tenant_id, "name": "Unknown", "plan_id": None}
            
            # Create tenant info
            tenant_info = {
                "id": org.id,
                "name": org.name,
                "plan_id": org.plan_id
            }
            
            # Cache the info (with a small cache to prevent memory issues)
            if len(self._tenant_cache) > 1000:  # Limit cache size
                self._tenant_cache.clear()
            self._tenant_cache[tenant_id] = tenant_info
            
            return tenant_info
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tenant info: {str(e)}")
            return {"id": tenant_id, "name": "Unknown", "plan_id": None}
    
    def _get_excluded_paths(self) -> List[str]:
        """Get list of paths excluded from tenant context"""
        return [
            "/",
            f"{settings.API_V1_STR}/docs",
            f"{settings.API_V1_STR}/redoc",
            f"{settings.API_V1_STR}/openapi.json",
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/auth/",
        ]
    
    def is_path_excluded(self, path: str) -> bool:
        """Check if a path should be excluded from tenant context"""
        return any(path.startswith(excluded) for excluded in self._excluded_paths)
    
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
                tenant_id = int(request.headers["X-Tenant-ID"])
                # Validate tenant exists (optionally)
                # This could be enhanced to check if the user has access to this tenant
                return tenant_id
            except (ValueError, TypeError):
                logger.warning(f"Invalid X-Tenant-ID header: {request.headers['X-Tenant-ID']}")
                return None
        
        # Check for authenticated user
        user = getattr(request.state, "user", None)
        if isinstance(user, User) and user.organization_id:
            return user.organization_id
            
        return None