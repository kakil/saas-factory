from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship

from app.core.db.base import Base

# Association table for user-team many-to-many relationship
user_team = Table(
    "user_team",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("team_id", Integer, ForeignKey("teams.id")),
)


class Organization(Base):
    """
    Organization model representing a tenant in the system
    """
    __tablename__ = "organizations"

    name = Column(String, index=True, nullable=False)
    plan_id = Column(String, index=True)  # Subscription plan ID

    # Relationships
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    members = relationship("User", back_populates="organization")

    def __str__(self) -> str:
        return f"Organization(id={self.id}, name={self.name})"


class Team(Base):
    """
    Team model representing a group of users within an organization
    """
    __tablename__ = "teams"

    name = Column(String, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    description = Column(String, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("User", secondary=user_team, back_populates="teams")

    def __str__(self) -> str:
        return f"Team(id={self.id}, name={self.name})"