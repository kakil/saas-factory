import os
from typing import Optional, Generator, Dict, Any

import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.security.supabase import supabase_auth
from app.features.users.models import User
from app.features.users.repository import get_user_repository, UserRepository
from app.features.users.schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_current_user_supabase(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        user_repository: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Dependency to get the current authenticated user using Supabase Auth
    """
    try:
        # Verify with Supabase
        user_data = await supabase_auth.verify_token(token)
        
        # Get Supabase user ID and email
        supabase_uid = user_data.get("id")
        email = user_data.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Find or create user in our database
        user = user_repository.get_by_email(email=email)
        
        if not user:
            # This means the user exists in Supabase but not in our database
            # You might want to handle this differently based on your user flow
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in application database",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Store Supabase user ID in request state
        # This could be useful for other operations
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_jwt(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Legacy dependency to get the current authenticated user using our JWT
    """
    try:
        # Verify JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.email == token_data.sub).first()
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


# Set the current authentication method
# During transition, you can toggle between the two methods
get_current_user = get_current_user_supabase


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
    # Get tenant from JWT claims or subdomain or header
    if "X-Tenant-ID" in request.headers:
        return int(request.headers["X-Tenant-ID"])

    # Get from JWT token
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "organization_id"):
        return user.organization_id

    raise HTTPException(status_code=400, detail="Tenant ID not found")


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