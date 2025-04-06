from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db.base import Base


class PaymentStatus(str, PyEnum):
    """Payment statuses"""
    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"


class PaymentMethod(str, PyEnum):
    """Payment methods"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    SEPA = "sepa_debit"
    SOFORT = "sofort"
    PAYPAL = "paypal"
    GIROPAY = "giropay"
    IDEAL = "ideal"
    BACS_DEBIT = "bacs_debit"
    ALIPAY = "alipay"
    WECHAT = "wechat"
    OTHER = "other"


class Payment(Base):
    """
    Payment model tracking payment transactions
    Maps to Stripe Payments
    """
    __tablename__ = "payments"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    stripe_payment_intent_id = Column(String, unique=True, index=True, nullable=True)
    stripe_payment_method_id = Column(String, index=True, nullable=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String, default="usd", nullable=False)
    status = Column(String, default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String, default=PaymentMethod.CARD, nullable=False)
    description = Column(String, nullable=True)
    failure_message = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    refunded = Column(Boolean, default=False, nullable=False)
    refunded_amount = Column(Numeric(precision=10, scale=2), default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
    
    def __str__(self) -> str:
        return f"Payment(id={self.id}, amount={self.amount}, status={self.status}, stripe_id={self.stripe_payment_intent_id})"