import os
from typing import Optional, Generator

import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from supabase import create_client, Client

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.features.users.models import User
from app.features.users.schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# Initialize Supabase client
supabase_url = settings.SUPABASE_URL
supabase_key = settings.SUPABASE_KEY
supabase: Client = create_client(supabase_url, supabase_key)


async def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current authenticated user
    """
    try:
        # Verify JWT with Supabase
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