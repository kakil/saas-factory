from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

from app.features.billing.models.plan import PlanInterval
from app.features.billing.models.price import PriceCurrency, PriceType


class PlanBase(BaseModel):
    """Base schema for Plan model"""
    name: str
    description: Optional[str] = None
    features: Optional[List[str]] = None
    is_public: bool = True
    metadata: Optional[Dict[str, Any]] = None


class PlanCreate(PlanBase):
    """Schema for creating a new plan"""
    pass


class PlanUpdate(BaseModel):
    """Schema for updating a plan"""
    name: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PriceBase(BaseModel):
    """Base schema for Price model"""
    amount: float
    currency: str = PriceCurrency.USD
    interval: Optional[str] = PlanInterval.MONTHLY
    price_type: str = PriceType.RECURRING
    metadata: Optional[Dict[str, Any]] = None


class PriceCreate(PriceBase):
    """Schema for creating a new price"""
    pass


class PriceResponse(PriceBase):
    """Schema for price response"""
    id: int
    plan_id: int
    stripe_price_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanResponse(PlanBase):
    """Schema for plan response"""
    id: int
    stripe_product_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    prices: Optional[List[PriceResponse]] = None

    class Config:
        from_attributes = True