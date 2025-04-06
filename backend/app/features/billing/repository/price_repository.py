from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.core.db.repository import BaseRepository
from app.features.billing.models.price import Price


class PriceRepository(BaseRepository[Price]):
    """
    Repository for Price model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Price)
    
    async def get_by_stripe_id(self, stripe_price_id: str) -> Optional[Price]:
        """
        Get a price by Stripe price ID
        
        Args:
            stripe_price_id: Stripe price ID
            
        Returns:
            Price object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_price_id == stripe_price_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_by_plan(self, plan_id: int, active_only: bool = True) -> List[Price]:
        """
        List prices for a plan
        
        Args:
            plan_id: Plan ID
            active_only: Whether to only include active prices
            
        Returns:
            List of prices
        """
        stmt = select(self.model).where(self.model.plan_id == plan_id)
        
        if active_only:
            stmt = stmt.where(self.model.is_active == True)
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_default_price_for_plan(self, plan_id: int) -> Optional[Price]:
        """
        Get the default price for a plan
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Default price or None if not found
        """
        # Get the first active price for the plan
        # In a real implementation, you might want to handle this differently
        # For example, by having a "is_default" flag on prices
        stmt = select(self.model).where(
            self.model.plan_id == plan_id,
            self.model.is_active == True
        ).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalars().first()