from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete
from sqlalchemy.orm import selectinload

from app.core.db.repository import BaseRepository
from app.features.billing.models.invoice import Invoice


class InvoiceRepository(BaseRepository[Invoice]):
    """
    Repository for Invoice model
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Invoice)
    
    async def get_by_stripe_id(self, stripe_invoice_id: str) -> Optional[Invoice]:
        """
        Get an invoice by Stripe invoice ID
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Invoice object or None if not found
        """
        stmt = select(self.model).where(self.model.stripe_invoice_id == stripe_invoice_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_with_items(self, invoice_id: int) -> Optional[Invoice]:
        """
        Get an invoice with its items
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice object with items or None if not found
        """
        stmt = select(self.model).where(self.model.id == invoice_id).options(selectinload(Invoice.items))
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_by_customer(self, customer_id: int, paid_only: bool = False, limit: int = 10) -> List[Invoice]:
        """
        List invoices for a customer
        
        Args:
            customer_id: Customer ID
            paid_only: Whether to only include paid invoices
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoices
        """
        stmt = select(self.model).where(self.model.customer_id == customer_id)
        
        if paid_only:
            stmt = stmt.where(self.model.paid == True)
            
        stmt = stmt.order_by(self.model.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())