from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.dependencies import get_current_user, get_admin_user
from app.features.users.models import User
from app.features.users.schemas import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserWithOrganization,
)
from app.features.users.service import UserService, get_user_service

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def read_current_user(
        current_user: User = Depends(get_current_user),
):
    """
    Get current user
    """
    return current_user


@router.patch("/me", response_model=UserSchema)
async def update_current_user(
        user_in: UserUpdate,
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    """
    Update current user
    """
    return user_service.update_user(user_id=current_user.id, user_in=user_in)


@router.patch("/me/settings", response_model=UserSchema)
async def update_user_settings(
        settings: Dict[str, Any],
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    """
    Update current user settings
    """
    return user_service.update_user_settings(user_id=current_user.id, settings=settings)


@router.get("", response_model=List[UserSchema])
async def read_users(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_admin_user),  # Only admin can list all users
        user_service: UserService = Depends(get_user_service),
):
    """
    Get all users (admin only)
    """
    return user_service.get_users(skip=skip, limit=limit)


@router.post("", response_model=UserSchema)
async def create_user(
        user_in: UserCreate,
        current_user: User = Depends(get_admin_user),  # Only admin can create users
        user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user (admin only)
    """
    return user_service.create_user(user_in=user_in)


@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    """
    Get a specific user
    """
    # Only allow admin users to access other user profiles
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    user = user_service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
        user_id: int,
        user_in: UserUpdate,
        current_user: User = Depends(get_admin_user),  # Only admin can update users
        user_service: UserService = Depends(get_user_service),
):
    """
    Update a user (admin only)
    """
    return user_service.update_user(user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
        user_id: int,
        current_user: User = Depends(get_admin_user),  # Only admin can delete users
        user_service: UserService = Depends(get_user_service),
):
    """
    Delete a user (admin only)
    """
    return user_service.delete_user(user_id=user_id)