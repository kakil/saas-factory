from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# Organization schemas
class OrganizationBase(BaseModel):
    name: str
    plan_id: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(OrganizationBase):
    name: Optional[str] = None


class OrganizationInDBBase(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Organization(OrganizationInDBBase):
    pass


class OrganizationWithDetails(Organization):
    member_count: int
    team_count: int


# Team schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: int


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    name: Optional[str] = None
    description: Optional[str] = None
    organization_id: Optional[int] = None


class TeamInDBBase(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Team(TeamInDBBase):
    pass


class TeamWithMembers(Team):
    member_count: int


# Team member schemas
class TeamMemberAdd(BaseModel):
    user_id: int


class TeamMemberRemove(BaseModel):
    user_id: int