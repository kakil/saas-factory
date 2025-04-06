from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

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


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response"""
    id: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    is_default: bool


class InvoiceListResponse(BaseModel):
    """Schema for simplified invoice in list response"""
    id: int
    stripe_invoice_id: Optional[str] = None
    status: str
    amount_due: float
    amount_paid: float
    created_at: datetime
    pdf_url: Optional[str] = None


class SubscriptionBriefResponse(BaseModel):
    """Schema for simplified subscription response"""
    active: bool
    status: Optional[str] = None
    period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    auto_renew: Optional[bool] = None


class OrganizationBriefResponse(BaseModel):
    """Schema for simplified organization response"""
    id: int
    name: str
    teams_count: int
    members_count: int


class OrganizationBillingResponse(BaseModel):
    """Schema for organization billing information"""
    customer: CustomerResponse
    organization: OrganizationBriefResponse
    subscription: SubscriptionBriefResponse
    payment_methods: List[PaymentMethodResponse]
    recent_invoices: List[InvoiceListResponse]
    
    class Config:
        from_attributes = True