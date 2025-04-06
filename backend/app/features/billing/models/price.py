from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db.base import Base


class PriceCurrency(str, PyEnum):
    """Supported currencies"""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"


class PriceType(str, PyEnum):
    """Price types"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    USAGE = "usage"


class Price(Base):
    """
    Price model defining the cost of plans
    Maps to Stripe Prices
    """
    __tablename__ = "prices"

    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    stripe_price_id = Column(String, unique=True, index=True, nullable=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String, default=PriceCurrency.USD, nullable=False)
    interval = Column(String, nullable=True)  # Can be null for one-time prices
    price_type = Column(String, default=PriceType.RECURRING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    plan = relationship("Plan", back_populates="prices")
    subscription_items = relationship("SubscriptionItem", back_populates="price")
    
    def __str__(self) -> str:
        return f"Price(id={self.id}, amount={self.amount}, currency={self.currency}, stripe_id={self.stripe_price_id})"