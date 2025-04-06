from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from app.features.billing.models.payment import PaymentStatus, PaymentMethod


class PaymentBase(BaseModel):
    """Base schema for Payment model"""
    customer_id: int
    amount: float
    currency: str = "usd"
    payment_method: str = PaymentMethod.CARD
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentCreate(BaseModel):
    """Schema for creating a new payment"""
    customer_id: int
    amount: int  # Amount in cents
    currency: str = "usd"
    payment_method_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    id: int
    invoice_id: Optional[int] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_payment_method_id: Optional[str] = None
    status: str
    failure_message: Optional[str] = None
    refunded: bool
    refunded_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True