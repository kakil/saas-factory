from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.security.auth import auth_service
from app.features.users.models import User
from app.features.users.repository import get_user_repository, UserRepository

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
    """
    # Check for tenant ID in header
    if "X-Tenant-ID" in request.headers:
        try:
            return int(request.headers["X-Tenant-ID"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid tenant ID format"
            )
    
    # Check for authenticated user
    user = getattr(request.state, "user", None)
    if isinstance(user, User) and user.organization_id:
        return user.organization_id
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tenant ID not found"
    )


async def set_tenant_context(
        request: Request,
        tenant_id: int = Depends(get_tenant_id),
        db: Session = Depends(get_db)
):
    """
    Set tenant context for request
    """
    # Set in database session
    db.execute(f"SET app.current_tenant = '{tenant_id}'")

    # Store in request state
    request.state.tenant_id = tenant_id

    return tenant_id