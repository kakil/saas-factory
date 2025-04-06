from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

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