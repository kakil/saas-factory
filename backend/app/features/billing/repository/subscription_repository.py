from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete
from sqlalchemy.orm import selectinload

from app.core.db.repository import BaseRepository
from app.features.billing.models.subscription import Subscription


class SubscriptionRepository(BaseRepository[Subscription]):
    """
    Repository for Subscription model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Subscription)
    
    async def get_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """
        Get a subscription by Stripe subscription ID
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Subscription object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_subscription_id == stripe_subscription_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_with_items(self, subscription_id: int) -> Optional[Subscription]:
        """
        Get a subscription with its items
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription object with items or None if not found
        """
        stmt = select(self.model).where(self.model.id == subscription_id).options(selectinload(Subscription.items))
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_by_customer(self, customer_id: int, active_only: bool = True) -> List[Subscription]:
        """
        List subscriptions for a customer
        
        Args:
            customer_id: Customer ID
            active_only: Whether to only include active subscriptions
            
        Returns:
            List of subscriptions
        """
        stmt = select(self.model).where(self.model.customer_id == customer_id)
        
        if active_only:
            stmt = stmt.where(self.model.status.in_(["active", "trialing"]))
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())