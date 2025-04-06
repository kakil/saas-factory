import logging
from typing import Any, Dict, List, Optional, Union

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.db.session import get_db
from app.features.billing.models.customer import Customer, CustomerTier
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.service.stripe_service import StripeService
from app.features.teams.models import Organization

logger = logging.getLogger(__name__)


class CustomerService:
    """
    Service for managing billing customers
    Handles creation, updating, and synchronization with Stripe
    """
    
    def __init__(self, db: AsyncSession, stripe_service: StripeService, customer_repository: CustomerRepository):
        self.db = db
        self.stripe_service = stripe_service
        self.customer_repository = customer_repository
    
    async def get_or_create_customer(self, organization_id: int) -> Customer:
        """
        Get an existing customer or create a new one for an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Customer object
            
        Raises:
            ValueError: If organization doesn't exist
        """
        # Check if customer already exists
        customer = await self.customer_repository.get_by_organization_id(organization_id)
        if customer:
            return customer
        
        # Get organization details
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await self.db.execute(stmt)
        organization = result.scalars().first()
        
        if not organization:
            raise ValueError(f"Organization with ID {organization_id} not found")
        
        # Create customer in Stripe
        stripe_customer = self.stripe_service.create_customer(
            email=organization.members[0].email if organization.members else None,
            name=organization.name,
            metadata={"organization_id": str(organization_id)}
        )
        
        # Create local customer record
        customer = Customer(
            organization_id=organization_id,
            stripe_customer_id=stripe_customer["id"],
            tier=CustomerTier.FREE,
            billing_name=organization.name,
            billing_email=organization.members[0].email if organization.members else None,
        )
        
        await self.customer_repository.create(customer)
        return customer
    
    async def update_customer(self, customer_id: int, **kwargs) -> Customer:
        """
        Update a customer's local and Stripe data
        
        Args:
            customer_id: Customer ID
            **kwargs: Fields to update
            
        Returns:
            Updated customer object
            
        Raises:
            ValueError: If customer doesn't exist
        """
        # Get customer
        customer = await self.customer_repository.get(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Fields to update in Stripe
        stripe_fields = {}
        local_fields = {}
        
        # Process kwargs
        for key, value in kwargs.items():
            if key in ["billing_email", "billing_name"]:
                # Update in both places
                stripe_fields["email" if key == "billing_email" else "name"] = value
                local_fields[key] = value
            elif key in ["billing_address", "tax_id", "tax_exempt", "metadata"]:
                # Update in both places
                stripe_fields[key.replace("billing_", "")] = value
                local_fields[key] = value
            elif key == "tier":
                # Only update locally
                local_fields[key] = value
            elif key == "default_payment_method_id":
                # Update in Stripe, store ID locally
                if value:
                    self.stripe_service.update_customer(
                        customer.stripe_customer_id,
                        invoice_settings={"default_payment_method": value}
                    )
                local_fields[key] = value
        
        # Update in Stripe if any fields to update
        if stripe_fields:
            try:
                self.stripe_service.update_customer(customer.stripe_customer_id, **stripe_fields)
            except stripe.error.StripeError as e:
                logger.error(f"Failed to update Stripe customer: {str(e)}")
                raise ValueError(f"Stripe error: {str(e)}")
        
        # Update locally
        if local_fields:
            customer = await self.customer_repository.update(customer_id, **local_fields)
        
        return customer
    
    async def get_customer_by_stripe_id(self, stripe_customer_id: str) -> Optional[Customer]:
        """
        Get a customer by Stripe customer ID
        
        Args:
            stripe_customer_id: Stripe customer ID
            
        Returns:
            Customer object or None if not found
        """
        return await self.customer_repository.get_by_stripe_id(stripe_customer_id)
    
    async def sync_customer(self, stripe_customer_id: str) -> Optional[Customer]:
        """
        Sync customer data from Stripe
        
        Args:
            stripe_customer_id: Stripe customer ID
            
        Returns:
            Updated customer object or None if not found
        """
        # Get customer by Stripe ID
        customer = await self.get_customer_by_stripe_id(stripe_customer_id)
        if not customer:
            logger.warning(f"Customer with Stripe ID {stripe_customer_id} not found in database")
            return None
        
        try:
            # Get data from Stripe
            stripe_customer = self.stripe_service.get_customer(stripe_customer_id)
            
            # Extract data
            update_data = {
                "billing_email": stripe_customer.get("email"),
                "billing_name": stripe_customer.get("name"),
                "tax_exempt": stripe_customer.get("tax_exempt", "none"),
                "metadata": stripe_customer.get("metadata", {}),
            }
            
            # Get default payment method
            if stripe_customer.get("invoice_settings", {}).get("default_payment_method"):
                update_data["default_payment_method_id"] = stripe_customer["invoice_settings"]["default_payment_method"]
            
            # Update local record
            customer = await self.customer_repository.update(customer.id, **update_data)
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync customer from Stripe: {str(e)}")
            return customer
    
    async def mark_customer_deleted(self, stripe_customer_id: str) -> bool:
        """
        Mark a customer as deleted in our database after Stripe deletion
        
        Args:
            stripe_customer_id: Stripe customer ID
            
        Returns:
            Success flag
        """
        # Find customer
        customer = await self.get_customer_by_stripe_id(stripe_customer_id)
        if not customer:
            logger.warning(f"Customer with Stripe ID {stripe_customer_id} not found in database")
            return False
        
        # Mark as deleted
        try:
            await self.customer_repository.update(
                customer.id,
                stripe_customer_id=f"deleted_{stripe_customer_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark customer as deleted: {str(e)}")
            return False
    
    async def handle_payment_method_attached(self, stripe_customer_id: str, payment_method_id: str) -> bool:
        """
        Handle payment method attachment webhook
        Sets as default if it's the first payment method
        
        Args:
            stripe_customer_id: Stripe customer ID
            payment_method_id: Payment method ID
            
        Returns:
            Success flag
        """
        # Get customer
        customer = await self.get_customer_by_stripe_id(stripe_customer_id)
        if not customer:
            logger.warning(f"Customer with Stripe ID {stripe_customer_id} not found in database")
            return False
        
        # Check if customer has a default payment method
        if not customer.default_payment_method_id:
            try:
                # Set as default in Stripe
                self.stripe_service.update_customer(
                    stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )
                
                # Update local record
                await self.customer_repository.update(
                    customer.id,
                    default_payment_method_id=payment_method_id
                )
                
                logger.info(f"Set payment method {payment_method_id} as default for customer {customer.id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to set default payment method: {str(e)}")
                return False
        
        return True
    
    async def handle_payment_method_detached(self, payment_method_id: str) -> bool:
        """
        Handle payment method detachment webhook
        Updates default payment method if needed
        
        Args:
            payment_method_id: Payment method ID
            
        Returns:
            Success flag
        """
        # Find customers with this payment method as default
        stmt = select(Customer).where(Customer.default_payment_method_id == payment_method_id)
        result = await self.db.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            # No customer using this as default
            return True
        
        try:
            # Get customer's payment methods
            payment_methods = self.stripe_service.list_payment_methods(customer.stripe_customer_id)
            
            if payment_methods["data"]:
                # Set first available as default
                new_default = payment_methods["data"][0]["id"]
                
                # Update in Stripe
                self.stripe_service.update_customer(
                    customer.stripe_customer_id,
                    invoice_settings={"default_payment_method": new_default}
                )
                
                # Update locally
                await self.customer_repository.update(
                    customer.id,
                    default_payment_method_id=new_default
                )
                
                logger.info(f"Updated default payment method to {new_default} for customer {customer.id}")
            else:
                # No payment methods left
                await self.customer_repository.update(
                    customer.id,
                    default_payment_method_id=None
                )
                
                logger.info(f"Cleared default payment method for customer {customer.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle payment method detachment: {str(e)}")
            return False