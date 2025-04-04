from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.dependencies import get_current_user, get_admin_user, get_tenant_repository, get_tenant_info
from app.features.teams.repository import TeamRepository, OrganizationRepository, get_team_repository, get_organization_repository
from app.features.teams.schemas import Organization, OrganizationCreate, Team, TeamCreate, TeamMember
from app.features.users.models import User

router = APIRouter()


# Organization API endpoints
@router.get("/organizations", response_model=List[Organization], tags=["organizations"])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get list of organizations
    Admin access only
    """
    repo = get_organization_repository(db)
    organizations = repo.get_multi(skip=skip, limit=limit)
    return organizations


@router.post("/organizations", response_model=Organization, tags=["organizations"])
def create_organization(
    organization_in: OrganizationCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Create new organization
    Admin access only
    """
    repo = get_organization_repository(db)
    organization = repo.create(obj_in=organization_in)
    return organization


@router.get("/organizations/{organization_id}", response_model=Organization, tags=["organizations"])
def get_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get organization by ID
    """
    # Regular users can only access their own organization
    if not current_user.is_superuser and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization",
        )
        
    repo = get_organization_repository(db)
    organization = repo.get(id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return organization


# Team API endpoints
# Use the new tenant-aware repository pattern with get_tenant_repository
get_tenant_team_repo = get_tenant_repository(lambda db: TeamRepository(Team, db))


@router.get(f"{settings.API_V1_STR}/teams", response_model=List[Team])
def get_teams(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    repo: TeamRepository = Depends(get_tenant_team_repo),
    tenant_info: dict = Depends(get_tenant_info),
):
    """
    Get teams for current tenant
    
    Uses the tenant-aware repository which automatically filters by organization (tenant).
    The tenant context is extracted from the authenticated user or X-Tenant-ID header.
    """
    teams = repo.get_by_organization(skip=skip, limit=limit)
    return teams


@router.post(f"{settings.API_V1_STR}/teams", response_model=Team)
def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(get_current_user),
    repo: TeamRepository = Depends(get_tenant_team_repo),
    tenant_info: dict = Depends(get_tenant_info),
):
    """
    Create new team in current tenant
    
    The team is automatically assigned to the current tenant and tenant
    isolation ensures users can only create teams in their own tenant.
    """
    # Team is automatically assigned to current tenant context
    team = repo.create(obj_in=team_in)
    return team


@router.get(f"{settings.API_V1_STR}/teams/{{team_id}}", response_model=Team)
def get_team(
    team_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Get team by ID
    
    Tenant isolation ensures users can only access teams in their tenant.
    """
    team = repo.get(id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return team


@router.get(f"{settings.API_V1_STR}/teams/{{team_id}}/members", response_model=List[TeamMember])
def get_team_members(
    team_id: int,
    skip: int = 0,
    limit: int = 100,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Get team members
    
    Tenant isolation ensures users can only access teams in their tenant.
    """
    members = repo.get_members(team_id=team_id, skip=skip, limit=limit)
    return [TeamMember(id=m.id, email=m.email, name=m.name) for m in members]


@router.post(f"{settings.API_V1_STR}/teams/{{team_id}}/members/{{user_id}}", response_model=dict)
def add_team_member(
    team_id: int,
    user_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Add user to team
    
    Tenant isolation ensures users can only modify teams in their tenant.
    """
    success = repo.add_member(team_id=team_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team or user not found",
        )
    return {"status": "success", "message": "User added to team"}


@router.delete(f"{settings.API_V1_STR}/teams/{{team_id}}/members/{{user_id}}", response_model=dict)
def remove_team_member(
    team_id: int,
    user_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Remove user from team
    
    Tenant isolation ensures users can only modify teams in their tenant.
    """
    success = repo.remove_member(team_id=team_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not in team",
        )
    return {"status": "success", "message": "User removed from team"}