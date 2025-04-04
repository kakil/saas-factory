from typing import Optional, Dict, Any, Type, TypeVar, Generic, Callable
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.db.repository import BaseRepository
from app.core.security.auth import auth_service
from app.features.users.models import User
from app.features.teams.models import Organization
from app.features.users.repository import get_user_repository, UserRepository

# Type variables for repository patterns
ModelType = TypeVar("ModelType")
RepoType = TypeVar("RepoType", bound=BaseRepository)

# Setup OAuth2 for Swagger UI / OpenAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

logger = logging.getLogger(__name__)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user
    
    This function leverages the auth_service to validate the token
    and extract user information regardless of the authentication provider.
    """
    try:
        # Get user info from token
        user_info = await auth_service.get_user_info(token)
        
        # Get user from database
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token content",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get an admin user
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_tenant_id(request: Request) -> int:
    """
    Extract tenant ID from request
    
    Order of precedence:
    1. Tenant ID from request state (set by middleware)
    2. X-Tenant-ID header
    3. User's organization_id from authenticated user
    """
    # Check for tenant ID in request state (already set by middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return tenant_id
    
    # Check for tenant ID in header
    if "X-Tenant-ID" in request.headers:
        try:
            return int(request.headers["X-Tenant-ID"])
        except (ValueError, TypeError):
            logger.warning(f"Invalid X-Tenant-ID header: {request.headers['X-Tenant-ID']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid tenant ID format"
            )
    
    # Check for authenticated user
    user = getattr(request.state, "user", None)
    if isinstance(user, User) and user.organization_id:
        return user.organization_id
    
    # Tenant ID required but not found
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tenant ID not found"
    )


async def get_optional_tenant_id(request: Request) -> Optional[int]:
    """
    Extract tenant ID from request, but don't require it
    """
    try:
        return await get_tenant_id(request)
    except HTTPException:
        # Tenant ID not found, but it's optional
        return None


async def get_tenant_info(
    request: Request,
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get information about the current tenant
    """
    # Check if tenant info already in request state
    if hasattr(request.state, "tenant_info"):
        return request.state.tenant_info
    
    # Fetch organization information
    org = db.query(Organization).filter(Organization.id == tenant_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    
    # Return tenant info
    tenant_info = {
        "id": org.id,
        "name": org.name,
        "plan_id": org.plan_id
    }
    
    # Store in request state
    request.state.tenant_info = tenant_info
    
    return tenant_info


async def set_tenant_context(
    request: Request,
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> int:
    """
    Set tenant context for request
    
    This dependency can be used to explicitly set tenant context in
    handlers that need it, though typically the middleware handles this.
    """
    try:
        # Set in database session
        db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))

        # Store in request state
        request.state.tenant_id = tenant_id

        # Get and store tenant info
        org = db.query(Organization).filter(Organization.id == tenant_id).first()
        if org:
            request.state.tenant_info = {
                "id": org.id,
                "name": org.name,
                "plan_id": org.plan_id
            }
            
        return tenant_id
    except SQLAlchemyError as e:
        logger.error(f"Database error setting tenant context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting tenant context"
        )


def get_tenant_repository(
    repository_factory: Callable[[Session], RepoType], 
    tenant_aware: bool = True
) -> Callable[[Request, Session], RepoType]:
    """
    Creates a dependency that returns a tenant-aware repository
    
    This factory function allows easy creation of tenant-aware repositories
    that automatically filter by the current tenant context.
    
    Example:
        get_user_repo = get_tenant_repository(lambda db: UserRepository(db))
        
        @app.get("/users")
        def get_users(repo: UserRepository = Depends(get_user_repo)):
            return repo.get_multi()  # Automatically filtered by tenant
    """
    async def _get_tenant_repository(
        request: Request,
        db: Session = Depends(get_db)
    ) -> RepoType:
        # Create base repository
        repo = repository_factory(db)
        
        # Tenant aware repositories need tenant context
        if tenant_aware:
            try:
                # Try to get tenant ID from request (might be optional)
                tenant_id = getattr(request.state, "tenant_id", None)
                
                if tenant_id:
                    # Set tenant ID in repository for filtering
                    repo.set_tenant_id(tenant_id)
            except Exception as e:
                logger.warning(f"Error setting tenant context in repository: {str(e)}")
                
        return repo
        
    return _get_tenant_repository