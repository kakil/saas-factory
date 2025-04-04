from typing import List, Optional, Dict, Any
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload
import logging

from app.core.db.repository import BaseRepository, with_tenant_context
from app.features.teams.models import Organization, Team, user_team
from app.features.teams.schemas import OrganizationCreate, OrganizationUpdate, TeamCreate, \
    TeamUpdate
from app.features.users.models import User

logger = logging.getLogger(__name__)


class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    """
    Repository for Organization model with custom methods
    
    This repository is typically not tenant-filtered since organizations
    are the tenants themselves.
    """
    
    def __init__(self, model: Organization, db: Session):
        # Organizations are generally not tenant-filtered
        super().__init__(model, db, tenant_aware=False)

    def get_with_details(self, *, id: int) -> Optional[Dict[str, Any]]:
        """
        Get organization with member and team counts
        """
        org = self.get(id=id)
        if not org:
            return None

        # Count members
        member_count = self.db.query(func.count(User.id)).filter(
            User.organization_id == id).scalar() or 0

        # Count teams
        team_count = self.db.query(func.count(Team.id)).filter(Team.organization_id == id).scalar() or 0

        # Convert to dict and remove SQLAlchemy state
        org_dict = {k: v for k, v in org.__dict__.items() if not k.startswith('_')}
        
        return {
            **org_dict,
            "member_count": member_count,
            "team_count": team_count
        }

    def get_members(self, *, id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get organization members
        """
        return self.db.query(User).filter(User.organization_id == id).offset(skip).limit(
            limit).all()
    
    def get_current_tenant_org(self) -> Optional[Organization]:
        """
        Get the organization for the current tenant context
        
        This is useful when you need to get the current tenant organization
        without knowing its ID explicitly.
        """
        try:
            # Get current tenant from database context
            result = self.db.execute(text("SELECT app.current_tenant_id()"))
            tenant_id = result.scalar()
            
            if tenant_id:
                return self.get(id=tenant_id)
            return None
        except Exception as e:
            logger.warning(f"Error getting current tenant organization: {str(e)}")
            return None


class TeamRepository(BaseRepository[Team, TeamCreate, TeamUpdate]):
    """
    Repository for Team model with multi-tenant support
    
    This repository applies tenant isolation to ensure teams are only
    accessible within their organization (tenant).
    """

    @with_tenant_context
    def get_with_members(self, *, id: int) -> Optional[Dict[str, Any]]:
        """
        Get team with member count, applying tenant isolation
        """
        team = self.get(id=id)
        if not team:
            return None

        # Count members
        member_count = self.db.query(func.count(user_team.c.user_id)).filter(
            user_team.c.team_id == id).scalar() or 0

        # Convert to dict and remove SQLAlchemy state
        team_dict = {k: v for k, v in team.__dict__.items() if not k.startswith('_')}
        
        return {
            **team_dict,
            "member_count": member_count
        }

    @with_tenant_context
    def get_members(self, *, team_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get team members, filtered by tenant context
        """
        # Apply tenant context to ensure we only see teams from current tenant
        team_query = self.db.query(Team)
        team_query = self._apply_tenant_filter(team_query)
        team = team_query.filter(Team.id == team_id).first()
        
        if not team:
            return []
        
        return (
            self.db.query(User)
            .join(user_team)
            .filter(user_team.c.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @with_tenant_context
    def add_member(self, *, team_id: int, user_id: int) -> bool:
        """
        Add a member to the team, respecting tenant isolation
        """
        # Apply tenant context to ensure we only access teams from current tenant
        team_query = self.db.query(Team)
        team_query = self._apply_tenant_filter(team_query)
        team = team_query.filter(Team.id == team_id).first()
        
        if not team:
            logger.warning(f"Attempted to add member to team {team_id} outside tenant context")
            return False

        # Check that user exists and belongs to same organization
        user = self.db.query(User).filter(
            User.id == user_id,
            User.organization_id == team.organization_id
        ).first()
        
        if not user:
            logger.warning(f"User {user_id} not found or not in same organization as team {team_id}")
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

    @with_tenant_context
    def remove_member(self, *, team_id: int, user_id: int) -> bool:
        """
        Remove a member from the team, respecting tenant isolation
        """
        # Apply tenant context to ensure we only access teams from current tenant
        team_query = self.db.query(Team)
        team_query = self._apply_tenant_filter(team_query)
        team = team_query.filter(Team.id == team_id).first()
        
        if not team:
            logger.warning(f"Attempted to remove member from team {team_id} outside tenant context")
            return False
            
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
    
    @with_tenant_context
    def get_by_organization(self, *, skip: int = 0, limit: int = 100) -> List[Team]:
        """
        Get all teams for the current tenant
        
        This method applies tenant context automatically using the decorator.
        """
        query = self.db.query(self.model)
        query = self._apply_tenant_filter(query)
        return query.offset(skip).limit(limit).all()


def get_organization_repository(db: Session) -> OrganizationRepository:
    """
    Get an OrganizationRepository instance
    """
    return OrganizationRepository(Organization, db)


def get_team_repository(db: Session, tenant_aware: bool = True) -> TeamRepository:
    """
    Get a TeamRepository instance with optional tenant awareness
    
    Args:
        db: Database session
        tenant_aware: Whether to apply tenant filtering (default: True)
    """
    return TeamRepository(Team, db, tenant_aware=tenant_aware)