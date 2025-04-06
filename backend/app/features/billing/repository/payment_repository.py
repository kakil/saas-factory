from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete

from app.core.db.repository import BaseRepository
from app.features.billing.models.payment import Payment


class PaymentRepository(BaseRepository[Payment]):
    """
    Repository for Payment model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Payment)
    
    async def get_by_stripe_id(self, stripe_payment_intent_id: str) -> Optional[Payment]:
        """
        Get a payment by Stripe payment intent ID
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_payment_intent_id == stripe_payment_intent_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_by_customer(self, customer_id: int, limit: int = 10) -> List[Payment]:
        """
        List payments for a customer
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of payments to return
            
        Returns:
            List of payments
        """
        stmt = select(self.model).where(self.model.customer_id == customer_id)
        stmt = stmt.order_by(self.model.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def list_by_invoice(self, invoice_id: int) -> List[Payment]:
        """
        List payments for an invoice
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            List of payments
        """
        stmt = select(self.model).where(self.model.invoice_id == invoice_id)
        stmt = stmt.order_by(self.model.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())