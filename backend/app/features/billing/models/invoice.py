from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db.base import Base


class InvoiceStatus(str, PyEnum):
    """Invoice statuses"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class Invoice(Base):
    """
    Invoice model for tracking billing invoices
    Maps to Stripe Invoices
    """
    __tablename__ = "invoices"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    stripe_invoice_id = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default=InvoiceStatus.DRAFT, nullable=False)
    invoice_number = Column(String, unique=True, nullable=True)
    invoice_pdf = Column(String, nullable=True)  # URL to PDF
    currency = Column(String, default="usd", nullable=False)
    subtotal = Column(Numeric(precision=10, scale=2), nullable=False)
    tax = Column(Numeric(precision=10, scale=2), default=0, nullable=False)
    total = Column(Numeric(precision=10, scale=2), nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    amount_paid = Column(Numeric(precision=10, scale=2), default=0, nullable=False)
    amount_due = Column(Numeric(precision=10, scale=2), nullable=False)
    description = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription", backref="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")
    
    def __str__(self) -> str:
        return f"Invoice(id={self.id}, total={self.total}, status={self.status}, stripe_id={self.stripe_invoice_id})"


class InvoiceItem(Base):
    """
    Invoice item model for individual line items on an invoice
    Maps to Stripe Invoice Items
    """
    __tablename__ = "invoice_items"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    subscription_item_id = Column(Integer, ForeignKey("subscription_items.id"), nullable=True)
    stripe_invoice_item_id = Column(String, unique=True, index=True, nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    subscription_item = relationship("SubscriptionItem", backref="invoice_items")
    
    def __str__(self) -> str:
        return f"InvoiceItem(id={self.id}, amount={self.amount}, description={self.description})"