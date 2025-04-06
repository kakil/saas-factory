from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db.base import Base


class PlanInterval(str, PyEnum):
    """Subscription billing intervals"""
    MONTHLY = "month"
    QUARTERLY = "quarter"
    ANNUAL = "year"
    ONE_TIME = "one_time"


class Plan(Base):
    """
    Plan model defining product offerings
    Maps to Stripe Products
    """
    __tablename__ = "plans"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stripe_product_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)
    features = Column(JSON, nullable=True)  # JSON array of features
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    prices = relationship("Price", back_populates="plan", cascade="all, delete-orphan")
    
    def __str__(self) -> str:
        return f"Plan(id={self.id}, name={self.name}, stripe_id={self.stripe_product_id})"