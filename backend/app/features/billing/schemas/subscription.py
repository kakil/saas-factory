from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

from app.features.billing.models.subscription import SubscriptionStatus


class SubscriptionBase(BaseModel):
    """Base schema for Subscription model"""
    customer_id: int
    is_auto_renew: bool = True
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription"""
    customer_id: int
    price_id: int
    quantity: int = 1
    trial_days: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    is_auto_renew: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    
class SubscriptionUpgrade(BaseModel):
    """Schema for upgrading or downgrading a subscription"""
    plan_id: int
    effective_date: Optional[datetime] = None
    prorate: bool = True
    maintain_trial: bool = True
    
    
class SubscriptionSchedule(BaseModel):
    """Schema for scheduling a future subscription update"""
    plan_id: int
    scheduled_date: datetime
    prorate: bool = True
    
    
class CouponApply(BaseModel):
    """Schema for applying a coupon to a subscription"""
    coupon_code: str = Field(..., min_length=1)


class SubscriptionItemResponse(BaseModel):
    """Schema for subscription item response"""
    id: int
    subscription_id: int
    price_id: int
    stripe_subscription_item_id: Optional[str] = None
    quantity: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response"""
    id: int
    stripe_subscription_id: Optional[str] = None
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: Optional[List[SubscriptionItemResponse]] = None

    class Config:
        from_attributes = True