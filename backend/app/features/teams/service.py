from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.features.teams.models import Organization, Team
from app.features.teams.repository import (
    OrganizationRepository, TeamRepository,
    get_organization_repository, get_team_repository
)
from app.features.teams.schemas import OrganizationCreate, OrganizationUpdate, TeamCreate, TeamUpdate


class OrganizationService:
    """
    Service for organization-related operations
    """
    def __init__(
            self,
            organization_repository: OrganizationRepository = Depends(get_organization_repository),
            db: Session = Depends(get_db),
    ):
        self.organization_repository = organization_repository
        self.db = db

    def get_organization(self, *, organization_id: int) -> Optional[Organization]:
        """
        Get an organization by ID
        """
        return self.organization_repository.get(id=organization_id)

    def get_organizations(self, *, skip: int = 0, limit: int = 100) -> List[Organization]:
        """
        Get multiple organizations
        """
        return self.organization_repository.get_multi(skip=skip, limit=limit)

    def create_organization(self, *, organization_in: OrganizationCreate) -> Organization:
        """
        Create a new organization
        """
        return self.organization_repository.create(obj_in=organization_in)

    def update_organization(
            self, *, organization_id: int, organization_in: OrganizationUpdate
    ) -> Optional[Organization]:
        """
        Update an organization
        """
        organization = self.organization_repository.get(id=organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return self.organization_repository.update(db_obj=organization, obj_in=organization_in)

    def delete_organization(self, *, organization_id: int) -> Optional[Organization]:
        """
        Delete an organization
        """
        organization = self.organization_repository.get(id=organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return self.organization_repository.delete(id=organization_id)


class TeamService:
    """
    Service for team-related operations
    """
    def __init__(
            self,
            team_repository: TeamRepository = Depends(get_team_repository),
            db: Session = Depends(get_db),
    ):
        self.team_repository = team_repository
        self.db = db

    def get_team(self, *, team_id: int) -> Optional[Team]:
        """
        Get a team by ID
        """
        return self.team_repository.get(id=team_id)

    def get_teams(self, *, organization_id: int, skip: int = 0, limit: int = 100) -> List[Team]:
        """
        Get teams for an organization
        """
        return self.team_repository.get_by_organization(
            organization_id=organization_id, skip=skip, limit=limit
        )

    def create_team(self, *, team_in: TeamCreate) -> Team:
        """
        Create a new team
        """
        return self.team_repository.create(obj_in=team_in)

    def update_team(self, *, team_id: int, team_in: TeamUpdate) -> Optional[Team]:
        """
        Update a team
        """
        team = self.team_repository.get(id=team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        return self.team_repository.update(db_obj=team, obj_in=team_in)

    def delete_team(self, *, team_id: int) -> Optional[Team]:
        """
        Delete a team
        """
        team = self.team_repository.get(id=team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        return self.team_repository.delete(id=team_id)

    def add_user_to_team(self, *, team_id: int, user_id: int) -> Team:
        """
        Add a user to a team
        """
        return self.team_repository.add_user(team_id=team_id, user_id=user_id)

    def remove_user_from_team(self, *, team_id: int, user_id: int) -> Team:
        """
        Remove a user from a team
        """
        return self.team_repository.remove_user(team_id=team_id, user_id=user_id)


def get_organization_service(
        organization_repository: OrganizationRepository = Depends(get_organization_repository),
        db: Session = Depends(get_db),
) -> OrganizationService:
    """
    Get an OrganizationService instance
    """
    return OrganizationService(organization_repository=organization_repository, db=db)


def get_team_service(
        team_repository: TeamRepository = Depends(get_team_repository),
        db: Session = Depends(get_db),
) -> TeamService:
    """
    Get a TeamService instance
    """
    return TeamService(team_repository=team_repository, db=db)