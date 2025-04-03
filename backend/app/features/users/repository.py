from typing import Optional, Dict, Any

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
        
    def get_by_supabase_uid(self, *, supabase_uid: str) -> Optional[User]:
        """
        Get a user by Supabase UID
        """
        return self.db.query(User).filter(User.supabase_uid == supabase_uid).first()

    def create_with_organization(self, *, obj_in: UserCreate, organization_id: int, supabase_uid: Optional[str] = None) -> User:
        """
        Create a user with organization
        """
        db_obj = User(
            email=obj_in.email,
            organization_id=organization_id,
            name=obj_in.name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            supabase_uid=supabase_uid,
        )
        db_obj.set_password(obj_in.password)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
        
    def create_from_supabase(self, *, email: str, supabase_uid: str, user_metadata: Dict[str, Any] = None) -> User:
        """
        Create a user from Supabase data
        """
        # Extract fields from user metadata
        user_metadata = user_metadata or {}
        name = user_metadata.get("name", "")
        is_superuser = user_metadata.get("is_superuser", False)
        
        # Create user with a placeholder password (since auth is delegated to Supabase)
        db_obj = User(
            email=email,
            name=name,
            is_active=True,
            is_superuser=is_superuser,
            supabase_uid=supabase_uid,
        )
        # Set a random password since we'll never use it directly
        db_obj.set_password(f"supabase_{supabase_uid}")
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


def get_user_repository(db: Session) -> UserRepository:
    """
    Get a UserRepository instance
    """
    return UserRepository(User, db)