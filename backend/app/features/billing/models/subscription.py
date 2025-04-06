from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db.base import Base


class SubscriptionStatus(str, PyEnum):
    """Subscription statuses"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ENDED = "ended"
    PAUSED = "paused"


class Subscription(Base):
    """
    Subscription model tracking active subscriptions
    Maps to Stripe Subscriptions
    """
    __tablename__ = "subscriptions"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default=SubscriptionStatus.INCOMPLETE, nullable=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    is_auto_renew = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    items = relationship("SubscriptionItem", back_populates="subscription", cascade="all, delete-orphan")
    
    def __str__(self) -> str:
        return f"Subscription(id={self.id}, status={self.status}, stripe_id={self.stripe_subscription_id})"


class SubscriptionItem(Base):
    """
    Subscription item model for individual subscription components
    Maps to Stripe Subscription Items
    """
    __tablename__ = "subscription_items"

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    price_id = Column(Integer, ForeignKey("prices.id"), nullable=False)
    stripe_subscription_item_id = Column(String, unique=True, index=True, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="items")
    price = relationship("Price", back_populates="subscription_items")
    
    def __str__(self) -> str:
        return f"SubscriptionItem(id={self.id}, quantity={self.quantity}, stripe_id={self.stripe_subscription_item_id})"