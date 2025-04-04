from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer

from app.core.dependencies import get_current_user, get_admin_user
from app.core.api.responses import success_response, error_response, paginated_response
from app.core.api.pagination import PaginationParams, paginate_query
from app.core.errors.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from app.features.users.models import User
from app.features.users.schemas import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserWithOrganization,
)
from app.features.users.service import UserService, get_user_service
from app.features.users.repository import UserRepository, get_user_repository

router = APIRouter()


@router.get("/me")
async def read_current_user(
        current_user: User = Depends(get_current_user),
):
    """
    Get current user
    """
    user_data = UserSchema.from_orm(current_user)
    return success_response(
        data=user_data.dict(),
        message="Current user retrieved successfully"
    )


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


@router.get("")
async def read_users(
        pagination: PaginationParams = Depends(),
        current_user: User = Depends(get_admin_user),  # Only admin can list all users
        user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get all users (admin only)
    
    This endpoint uses standardized pagination and response format.
    Returns a paginated list of users with metadata.
    """
    result = paginate_query(
        repo=user_repo,
        params=pagination,
        schema_cls=UserSchema
    )
    
    return paginated_response(
        items=[item.dict() for item in result.items],
        total=result.total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="Users retrieved successfully"
    )


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


@router.get("/{user_id}")
async def read_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    """
    Get a specific user
    
    This endpoint uses standardized error handling and response format.
    """
    # Only allow admin users to access other user profiles
    if user_id != current_user.id and not current_user.is_superuser:
        raise PermissionDeniedException(detail="Not enough permissions to access this user profile")

    user = user_service.get_user(user_id=user_id)
    if not user:
        raise NotFoundException(detail=f"User with ID {user_id} not found")
    
    user_data = UserSchema.from_orm(user)
    return success_response(
        data=user_data.dict(),
        message="User retrieved successfully"
    )


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