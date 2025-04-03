from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.db.repository import BaseRepository
from app.features.teams.models import Organization, Team, user_team
from app.features.teams.schemas import OrganizationCreate, OrganizationUpdate, TeamCreate, \
    TeamUpdate
from app.features.users.models import User


class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    """
    Repository for Organization model with custom methods
    """

    def get_with_details(self, *, id: int) -> Optional[dict]:
        """
        Get organization with member and team counts
        """
        org = self.get(id=id)
        if not org:
            return None

        # Count members
        member_count = self.db.query(func.count(User.id)).filter(
            User.organization_id == id).scalar()

        # Count teams
        team_count = self.db.query(func.count(Team.id)).filter(Team.organization_id == id).scalar()

        return {
            **org.__dict__,
            "member_count": member_count,
            "team_count": team_count
        }

    def get_members(self, *, id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get organization members
        """
        return self.db.query(User).filter(User.organization_id == id).offset(skip).limit(
            limit).all()


class TeamRepository(BaseRepository[Team, TeamCreate, TeamUpdate]):
    """
    Repository for Team model with custom methods
    """

    def get_with_members(self, *, id: int) -> Optional[dict]:
        """
        Get team with member count
        """
        team = self.get(id=id)
        if not team:
            return None

        # Count members
        member_count = self.db.query(func.count(user_team.c.user_id)).filter(
            user_team.c.team_id == id).scalar()

        return {
            **team.__dict__,
            "member_count": member_count
        }

    def get_members(self, *, team_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get team members
        """
        return (
            self.db.query(User)
            .join(user_team)
            .filter(user_team.c.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_member(self, *, team_id: int, user_id: int) -> bool:
        """
        Add a member to the team
        """
        team = self.get(id=team_id)
        if not team:
            return False

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Check if user is already a member
        is_member = (
            self.db.query(user_team)
            .filter(user_team.c.team_id == team_id, user_team.c.user_id == user_id)
            .first()
        )
        if is_member:
            return True  # Already a member

        # Add the association
        stmt = user_team.insert().values(team_id=team_id, user_id=user_id)
        self.db.execute(stmt)
        self.db.commit()
        return True

    def remove_member(self, *, team_id: int, user_id: int) -> bool:
        """
        Remove a member from the team
        """
        # Check if the association exists
        is_member = (
            self.db.query(user_team)
            .filter(user_team.c.team_id == team_id, user_team.c.user_id == user_id)
            .first()
        )
        if not is_member:
            return False  # Not a member

        # Remove the association
        stmt = user_team.delete().where(
            (user_team.c.team_id == team_id) & (user_team.c.user_id == user_id)
        )
        self.db.execute(stmt)
        self.db.commit()
        return True


def get_organization_repository(db: Session) -> OrganizationRepository:
    """
    Get an OrganizationRepository instance
    """
    return OrganizationRepository(Organization, db)


def get_team_repository(db: Session) -> TeamRepository:
    """
    Get a TeamRepository instance
    """
    return TeamRepository(Team, db)