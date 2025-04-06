from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.features.billing.models.customer import CustomerTier


class CustomerBase(BaseModel):
    """Base schema for Customer model"""
    organization_id: int
    tier: Optional[str] = CustomerTier.FREE
    billing_email: Optional[EmailStr] = None
    billing_name: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    tax_id: Optional[str] = None
    tax_exempt: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    tier: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_name: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    tax_id: Optional[str] = None
    tax_exempt: Optional[bool] = None
    default_payment_method_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: int
    stripe_customer_id: Optional[str] = None
    default_payment_method_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True