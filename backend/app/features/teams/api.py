from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.dependencies import get_current_user, get_admin_user, get_tenant_repository, get_tenant_info
from app.core.api.responses import success_response, error_response, paginated_response
from app.core.api.pagination import PaginationParams, paginate_query
from app.core.errors.exceptions import NotFoundException, PermissionDeniedException, ValidationException
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


@router.get(f"{settings.API_V1_STR}/teams")
def get_teams(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    repo: TeamRepository = Depends(get_tenant_team_repo),
    tenant_info: dict = Depends(get_tenant_info),
):
    """
    Get teams for current tenant
    
    Uses the tenant-aware repository which automatically filters by organization (tenant).
    The tenant context is extracted from the authenticated user or X-Tenant-ID header.
    
    This endpoint uses standardized pagination and response format.
    """
    result = paginate_query(
        repo=repo,
        params=pagination,
        schema_cls=Team
    )
    
    return paginated_response(
        items=[item.dict() for item in result.items],
        total=result.total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="Teams retrieved successfully",
        meta={
            "tenant_id": tenant_info.get("tenant_id"),
            "tenant_name": tenant_info.get("tenant_name", "Unknown")
        }
    )


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


@router.get(f"{settings.API_V1_STR}/teams/{{team_id}}")
def get_team(
    team_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Get team by ID
    
    Tenant isolation ensures users can only access teams in their tenant.
    Uses standardized error handling and response format.
    """
    team = repo.get(id=team_id)
    if not team:
        raise NotFoundException(detail=f"Team with ID {team_id} not found")
    
    team_data = Team.from_orm(team)
    return success_response(
        data=team_data.dict(),
        message="Team retrieved successfully"
    )


@router.get(f"{settings.API_V1_STR}/teams/{{team_id}}/members")
def get_team_members(
    team_id: int,
    pagination: PaginationParams = Depends(),
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Get team members
    
    Tenant isolation ensures users can only access teams in their tenant.
    Uses standardized pagination and response format.
    """
    # Check if team exists
    team = repo.get(id=team_id)
    if not team:
        raise NotFoundException(detail=f"Team with ID {team_id} not found")
    
    # Get members with pagination
    members = repo.get_members(team_id=team_id, skip=pagination.skip, limit=pagination.limit)
    
    # Convert to schema
    member_data = [TeamMember(id=m.id, email=m.email, name=m.name).dict() for m in members]
    
    # Get total count (in a real implementation, this would be a separate count query)
    total = len(members)  # This is a simplification, in reality we'd do a count query
    
    return paginated_response(
        items=member_data,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="Team members retrieved successfully",
        meta={
            "team_id": team_id,
            "team_name": team.name
        }
    )


@router.post(f"{settings.API_V1_STR}/teams/{{team_id}}/members/{{user_id}}")
def add_team_member(
    team_id: int,
    user_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Add user to team
    
    Tenant isolation ensures users can only modify teams in their tenant.
    Uses standardized error handling and response format.
    """
    success = repo.add_member(team_id=team_id, user_id=user_id)
    if not success:
        raise NotFoundException(detail="Team or user not found")
    
    return success_response(
        message="User added to team successfully",
        data={
            "team_id": team_id,
            "user_id": user_id
        }
    )


@router.delete(f"{settings.API_V1_STR}/teams/{{team_id}}/members/{{user_id}}")
def remove_team_member(
    team_id: int,
    user_id: int,
    repo: TeamRepository = Depends(get_tenant_team_repo),
):
    """
    Remove user from team
    
    Tenant isolation ensures users can only modify teams in their tenant.
    Uses standardized error handling and response format.
    """
    success = repo.remove_member(team_id=team_id, user_id=user_id)
    if not success:
        raise NotFoundException(detail="User not in team")
    
    return success_response(
        message="User removed from team successfully",
        data={
            "team_id": team_id,
            "user_id": user_id
        }
    )