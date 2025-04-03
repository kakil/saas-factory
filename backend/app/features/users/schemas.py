from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, EmailStr, Field, validator


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    organization_id: Optional[int] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Additional properties stored in DB
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    settings: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


# Login request schema
class Login(BaseModel):
    email: EmailStr
    password: str


# User with organization details
class UserWithOrganization(User):
    organization_name: Optional[str] = None


# User registration schema
class UserRegistration(UserCreate):
    organization_name: Optional[str] = None