from typing import List, Optional, Dict, Any
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.security.jwt import create_access_token
from app.features.users.models import User
from app.features.users.repository import UserRepository, get_user_repository
from app.features.users.schemas import UserCreate, UserUpdate, Token, Login
from app.features.teams.repository import OrganizationRepository, get_organization_repository


class UserService:
    """
    Service for user-related operations
    """

    def __init__(
            self,
            user_repository: UserRepository = Depends(get_user_repository),
            organization_repository: OrganizationRepository = Depends(get_organization_repository),
            db: Session = Depends(get_db),
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.db = db

    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password
        """
        user = self.user_repository.get_by_email(email=email)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    def create_access_token(self, user: User) -> Token:
        """
        Create access token for user
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )
        return Token(access_token=access_token)

    def login(self, *, login_data: Login) -> Token:
        """
        Login a user
        """
        user = self.authenticate(email=login_data.email, password=login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.create_access_token(user)

    def get_user(self, *, user_id: int) -> Optional[User]:
        """
        Get a user by ID
        """
        return self.user_repository.get(id=user_id)

    def get_by_email(self, *, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        return self.user_repository.get_by_email(email=email)

    def get_users(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get multiple users
        """
        return self.user_repository.get_multi(skip=skip, limit=limit)

    def create_user(self, *, user_in: UserCreate) -> User:
        """
        Create a new user
        """
        # Check if user with this email already exists
        user = self.user_repository.get_by_email(email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Create the user
        return self.user_repository.create(obj_in=user_in)

    def create_user_with_organization(
            self, *, user_in: UserCreate, organization_id: int
    ) -> User:
        """
        Create a user associated with an organization
        """
        # Check if user with this email already exists
        user = self.user_repository.get_by_email(email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Check if organization exists
        organization = self.organization_repository.get(id=organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Create the user with organization
        return self.user_repository.create_with_organization(
            obj_in=user_in, organization_id=organization_id
        )

    def update_user(self, *, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """
        Update a user
        """
        user = self.user_repository.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # If email is being updated, check for duplicates
        if user_in.email and user_in.email != user.email:
            existing_user = self.user_repository.get_by_email(email=user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

        return self.user_repository.update(db_obj=user, obj_in=user_in)

    def delete_user(self, *, user_id: int) -> Optional[User]:
        """
        Delete a user
        """
        user = self.user_repository.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return self.user_repository.delete(id=user_id)

    def update_user_settings(self, *, user_id: int, settings: Dict[str, Any]) -> Optional[User]:
        """
        Update user settings
        """
        user = self.user_repository.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Merge existing settings with updates
        current_settings = user.settings or {}
        current_settings.update(settings)

        return self.user_repository.update(
            db_obj=user, obj_in={"settings": current_settings}
        )


def get_user_service(
        user_repository: UserRepository = Depends(get_user_repository),
        organization_repository: OrganizationRepository = Depends(get_organization_repository),
        db: Session = Depends(get_db),
) -> UserService:
    """
    Get a UserService instance
    """
    return UserService(
        user_repository=user_repository,
        organization_repository=organization_repository,
        db=db,
    )