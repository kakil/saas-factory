from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete

from app.core.db.repository import BaseRepository
from app.features.billing.models.customer import Customer


class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for Customer model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Customer)
    
    async def get_by_organization_id(self, organization_id: int) -> Optional[Customer]:
        """
        Get a customer by organization ID
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Customer object or None if not found
        """
        stmt = select(self.model).where(self.model.organization_id == organization_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_stripe_id(self, stripe_customer_id: str) -> Optional[Customer]:
        """
        Get a customer by Stripe customer ID
        
        Args:
            stripe_customer_id: Stripe customer ID
            
        Returns:
            Customer object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_customer_id == stripe_customer_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()