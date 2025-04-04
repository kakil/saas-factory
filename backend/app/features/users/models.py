from datetime import datetime, timedelta
import secrets
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime
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
    
    # Email verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, unique=True, index=True, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String, unique=True, index=True, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

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
        
    def generate_verification_token(self) -> str:
        """
        Generate a verification token for email verification.
        
        Returns:
            The verification token
        """
        token = secrets.token_urlsafe(32)
        self.verification_token = token
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        self.is_verified = False
        return token
        
    def verify_email(self, token: str) -> bool:
        """
        Verify the user's email with the given token.
        
        Args:
            token: The verification token
            
        Returns:
            Whether verification was successful
        """
        if (
            self.verification_token == token and
            self.verification_token_expires and
            self.verification_token_expires > datetime.utcnow()
        ):
            self.is_verified = True
            self.verification_token = None
            self.verification_token_expires = None
            return True
        return False
        
    def generate_password_reset_token(self) -> str:
        """
        Generate a password reset token.
        
        Returns:
            The password reset token
        """
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return token
        
    def verify_password_reset_token(self, token: str) -> bool:
        """
        Verify the password reset token.
        
        Args:
            token: The password reset token
            
        Returns:
            Whether the token is valid
        """
        return (
            self.reset_token == token and
            self.reset_token_expires and
            self.reset_token_expires > datetime.utcnow()
        )