from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from app.features.billing.models.invoice import InvoiceStatus


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item response"""
    id: int
    invoice_id: int
    subscription_item_id: Optional[int] = None
    stripe_invoice_item_id: Optional[str] = None
    description: str
    quantity: int
    unit_price: float
    amount: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: int
    customer_id: int
    subscription_id: Optional[int] = None
    stripe_invoice_id: Optional[str] = None
    status: str
    invoice_number: Optional[str] = None
    invoice_pdf: Optional[str] = None
    currency: str
    subtotal: float
    tax: float
    total: float
    paid: bool
    amount_paid: float
    amount_due: float
    description: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    items: Optional[List[InvoiceItemResponse]] = None

    class Config:
        from_attributes = True