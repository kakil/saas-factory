import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.features.billing.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.features.billing.models.payment import Payment, PaymentStatus
from app.features.billing.repository.invoice_repository import InvoiceRepository
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.service.stripe_service import StripeService

logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Service for managing invoices
    Handles creation, payment, and synchronization with Stripe
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        stripe_service: StripeService,
        invoice_repository: InvoiceRepository,
        customer_repository: CustomerRepository
    ):
        self.db = db
        self.stripe_service = stripe_service
        self.invoice_repository = invoice_repository
        self.customer_repository = customer_repository
    
    async def get_invoice_by_stripe_id(self, stripe_invoice_id: str) -> Optional[Invoice]:
        """
        Get an invoice by Stripe invoice ID
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Invoice object or None if not found
        """
        stmt = select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def sync_invoice(self, stripe_invoice_id: str) -> Optional[Invoice]:
        """
        Sync invoice data from Stripe
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Updated invoice object or None if not found
        """
        try:
            # Get invoice from Stripe
            stripe_invoice = self.stripe_service.get_invoice(stripe_invoice_id)
            
            # Find or create invoice
            invoice = await self.get_invoice_by_stripe_id(stripe_invoice_id)
            
            if not invoice:
                # This is a new invoice, create it
                # First, find the customer
                stripe_customer_id = stripe_invoice.get("customer")
                if not stripe_customer_id:
                    logger.error(f"Invoice {stripe_invoice_id} has no customer ID")
                    return None
                
                customer = await self.customer_repository.get_by_stripe_id(stripe_customer_id)
                if not customer:
                    logger.error(f"Customer with Stripe ID {stripe_customer_id} not found")
                    return None
                
                # Create invoice record
                invoice = Invoice(
                    customer_id=customer.id,
                    stripe_invoice_id=stripe_invoice_id,
                    status=stripe_invoice["status"],
                    invoice_number=stripe_invoice.get("number"),
                    invoice_pdf=stripe_invoice.get("invoice_pdf"),
                    currency=stripe_invoice["currency"],
                    subtotal=stripe_invoice["subtotal"] / 100.0,  # Convert from cents
                    tax=stripe_invoice["tax"] / 100.0 if stripe_invoice.get("tax") else 0,
                    total=stripe_invoice["total"] / 100.0,
                    paid=stripe_invoice["paid"],
                    amount_paid=stripe_invoice["amount_paid"] / 100.0,
                    amount_due=stripe_invoice["amount_due"] / 100.0,
                    description=stripe_invoice.get("description"),
                    metadata=stripe_invoice.get("metadata", {}),
                )
                
                # Add period dates if available
                if stripe_invoice.get("period_start"):
                    invoice.period_start = datetime.fromtimestamp(stripe_invoice["period_start"])
                
                if stripe_invoice.get("period_end"):
                    invoice.period_end = datetime.fromtimestamp(stripe_invoice["period_end"])
                
                # Add due date if available
                if stripe_invoice.get("due_date"):
                    invoice.due_date = datetime.fromtimestamp(stripe_invoice["due_date"])
                
                # Add subscription ID if available
                if stripe_invoice.get("subscription"):
                    # Find subscription by Stripe ID
                    stmt = (
                        select(Subscription)
                        .where(Subscription.stripe_subscription_id == stripe_invoice["subscription"])
                    )
                    result = await self.db.execute(stmt)
                    subscription = result.scalars().first()
                    
                    if subscription:
                        invoice.subscription_id = subscription.id
                
                # Create invoice
                invoice = await self.invoice_repository.create(invoice)
                
                # Create invoice items
                for item in stripe_invoice["lines"]["data"]:
                    # Create invoice item
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        stripe_invoice_item_id=item["id"],
                        description=item.get("description", "Subscription item"),
                        quantity=item.get("quantity", 1),
                        unit_price=item["unit_amount"] / 100.0 if item.get("unit_amount") else 0,
                        amount=item["amount"] / 100.0,
                    )
                    
                    # Add subscription item reference if available
                    if item.get("subscription_item"):
                        # Find subscription item by Stripe ID
                        stmt = (
                            select(SubscriptionItem)
                            .where(SubscriptionItem.stripe_subscription_item_id == item["subscription_item"])
                        )
                        result = await self.db.execute(stmt)
                        subscription_item = result.scalars().first()
                        
                        if subscription_item:
                            invoice_item.subscription_item_id = subscription_item.id
                    
                    self.db.add(invoice_item)
                
                await self.db.commit()
                
                # If invoice is already paid, update paid_at
                if invoice.paid:
                    await self.invoice_repository.update(
                        invoice.id, 
                        paid_at=datetime.now()
                    )
                
                return invoice
            
            # Update existing invoice
            update_data = {
                "status": stripe_invoice["status"],
                "invoice_number": stripe_invoice.get("number"),
                "invoice_pdf": stripe_invoice.get("invoice_pdf"),
                "subtotal": stripe_invoice["subtotal"] / 100.0,
                "tax": stripe_invoice["tax"] / 100.0 if stripe_invoice.get("tax") else 0,
                "total": stripe_invoice["total"] / 100.0,
                "paid": stripe_invoice["paid"],
                "amount_paid": stripe_invoice["amount_paid"] / 100.0,
                "amount_due": stripe_invoice["amount_due"] / 100.0,
                "description": stripe_invoice.get("description"),
                "metadata": stripe_invoice.get("metadata", {}),
            }
            
            # Update period dates if available
            if stripe_invoice.get("period_start"):
                update_data["period_start"] = datetime.fromtimestamp(stripe_invoice["period_start"])
            
            if stripe_invoice.get("period_end"):
                update_data["period_end"] = datetime.fromtimestamp(stripe_invoice["period_end"])
            
            # Update due date if available
            if stripe_invoice.get("due_date"):
                update_data["due_date"] = datetime.fromtimestamp(stripe_invoice["due_date"])
            
            # If newly paid, set paid_at
            if stripe_invoice["paid"] and not invoice.paid_at:
                update_data["paid_at"] = datetime.now()
            
            # Update invoice
            invoice = await self.invoice_repository.update(invoice.id, **update_data)
            
            # TODO: Sync invoice items if needed
            
            return invoice
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync invoice from Stripe: {str(e)}")
            return None
    
    async def mark_invoice_deleted(self, stripe_invoice_id: str) -> bool:
        """
        Mark an invoice as deleted in our database after Stripe deletion
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Success flag
        """
        # Find invoice
        invoice = await self.get_invoice_by_stripe_id(stripe_invoice_id)
        if not invoice:
            logger.warning(f"Invoice with Stripe ID {stripe_invoice_id} not found in database")
            return False
        
        # Mark as void
        try:
            await self.invoice_repository.update(
                invoice.id,
                status=InvoiceStatus.VOID
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark invoice as deleted: {str(e)}")
            return False
    
    async def handle_payment_succeeded(self, stripe_invoice_id: str) -> bool:
        """
        Handle invoice payment succeeded event
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Success flag
        """
        # Find or sync invoice
        invoice = await self.get_invoice_by_stripe_id(stripe_invoice_id)
        if not invoice:
            invoice = await self.sync_invoice(stripe_invoice_id)
            if not invoice:
                logger.error(f"Failed to sync invoice {stripe_invoice_id}")
                return False
        
        # Mark as paid
        try:
            await self.invoice_repository.update(
                invoice.id,
                status=InvoiceStatus.PAID,
                paid=True,
                paid_at=datetime.now()
            )
            
            # TODO: Send invoice paid notification
            
            return True
        except Exception as e:
            logger.error(f"Failed to mark invoice as paid: {str(e)}")
            return False
    
    async def handle_payment_failed(self, stripe_invoice_id: str) -> bool:
        """
        Handle invoice payment failed event
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Success flag
        """
        # Find or sync invoice
        invoice = await self.get_invoice_by_stripe_id(stripe_invoice_id)
        if not invoice:
            invoice = await self.sync_invoice(stripe_invoice_id)
            if not invoice:
                logger.error(f"Failed to sync invoice {stripe_invoice_id}")
                return False
        
        # TODO: Send payment failed notification
        
        return True
    
    async def handle_invoice_finalized(self, stripe_invoice_id: str) -> bool:
        """
        Handle invoice finalized event
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Success flag
        """
        # Find or sync invoice
        invoice = await self.get_invoice_by_stripe_id(stripe_invoice_id)
        if not invoice:
            invoice = await self.sync_invoice(stripe_invoice_id)
            if not invoice:
                logger.error(f"Failed to sync invoice {stripe_invoice_id}")
                return False
        
        # Update status
        try:
            await self.invoice_repository.update(
                invoice.id,
                status=InvoiceStatus.OPEN
            )
            
            # TODO: Send invoice finalized notification
            
            return True
        except Exception as e:
            logger.error(f"Failed to update invoice status: {str(e)}")
            return False