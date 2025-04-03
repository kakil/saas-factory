from typing import Optional

from sqlalchemy.orm import Session

from app.core.db.repository import BaseRepository
from app.features.users.models import User
from app.features.users.schemas import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with custom methods
    """

    def get_by_email(self, *, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        return self.db.query(User).filter(User.email == email).first()

    def create_with_organization(self, *, obj_in: UserCreate, organization_id: int) -> User:
        """
        Create a user with organization
        """
        db_obj = User(
            email=obj_in.email,
            organization_id=organization_id,
            name=obj_in.name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db_obj.set_password(obj_in.password)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


def get_user_repository(db: Session) -> UserRepository:
    """
    Get a UserRepository instance
    """
    return UserRepository(User, db)