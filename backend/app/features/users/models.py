from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.core.security.jwt import get_password_hash, verify_password


class User(Base):
    """
    User model representing a system user
    """
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    settings = Column(JSON, nullable=True)
    supabase_uid = Column(String, unique=True, index=True, nullable=True)  # Supabase User ID

    # Relationships
    organization = relationship("Organization", back_populates="members")
    teams = relationship("Team", secondary="user_team", back_populates="members")

    def set_password(self, password: str) -> None:
        """
        Set password hash from plain password
        """
        self.hashed_password = get_password_hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash
        """
        return verify_password(password, self.hashed_password)

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"