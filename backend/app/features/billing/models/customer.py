from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class CustomerTier(str, PyEnum):
    """Customer tiers for billing purposes"""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Customer(Base):
    """
    Customer model for billing purposes
    Each customer maps to an organization and contains Stripe-specific data
    """
    __tablename__ = "customers"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    tier = Column(String, default=CustomerTier.FREE, nullable=False)
    default_payment_method_id = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    billing_name = Column(String, nullable=True)
    billing_address = Column(JSON, nullable=True)
    tax_id = Column(String, nullable=True)
    tax_exempt = Column(Boolean, default=False, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="customer")
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    
    def __str__(self) -> str:
        return f"Customer(id={self.id}, organization_id={self.organization_id}, stripe_id={self.stripe_customer_id})"