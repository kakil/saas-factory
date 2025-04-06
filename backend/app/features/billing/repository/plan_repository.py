from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete
from sqlalchemy.orm import selectinload

from app.core.db.repository import BaseRepository
from app.features.billing.models.plan import Plan


class PlanRepository(BaseRepository[Plan]):
    """
    Repository for Plan model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Plan)
    
    async def get_by_stripe_id(self, stripe_product_id: str) -> Optional[Plan]:
        """
        Get a plan by Stripe product ID
        
        Args:
            stripe_product_id: Stripe product ID
            
        Returns:
            Plan object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_product_id == stripe_product_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_with_prices(self, plan_id: int) -> Optional[Plan]:
        """
        Get a plan with its prices
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan object with prices or None if not found
        """
        stmt = select(self.model).where(self.model.id == plan_id).options(selectinload(Plan.prices))
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_active(self, public_only: bool = True) -> List[Plan]:
        """
        List active plans
        
        Args:
            public_only: Whether to only include public plans
            
        Returns:
            List of active plans
        """
        stmt = select(self.model).where(self.model.is_active == True)
        
        if public_only:
            stmt = stmt.where(self.model.is_public == True)
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())