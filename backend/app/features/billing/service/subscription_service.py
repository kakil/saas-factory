import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.db.session import get_db
from app.features.billing.models.subscription import Subscription, SubscriptionItem, SubscriptionStatus
from app.features.billing.models.customer import Customer
from app.features.billing.models.price import Price
from app.features.billing.repository.subscription_repository import SubscriptionRepository
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.service.stripe_service import StripeService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing subscriptions
    Handles creation, updating, and synchronization with Stripe
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        stripe_service: StripeService,
        subscription_repository: SubscriptionRepository,
        customer_repository: CustomerRepository
    ):
        self.db = db
        self.stripe_service = stripe_service
        self.subscription_repository = subscription_repository
        self.customer_repository = customer_repository
    
    async def create_subscription(
        self,
        customer_id: int,
        price_id: int,
        quantity: int = 1,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        Create a new subscription for a customer
        
        Args:
            customer_id: Customer ID
            price_id: Price ID
            quantity: Number of units (default: 1)
            trial_days: Number of trial days (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Created subscription object
            
        Raises:
            ValueError: If customer or price doesn't exist
        """
        # Get customer
        customer = await self.customer_repository.get(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Get price
        stmt = select(Price).where(Price.id == price_id)
        result = await self.db.execute(stmt)
        price = result.scalars().first()
        
        if not price:
            raise ValueError(f"Price with ID {price_id} not found")
        
        # Create subscription in Stripe
        try:
            stripe_subscription = self.stripe_service.create_subscription(
                customer_id=customer.stripe_customer_id,
                price_id=price.stripe_price_id,
                quantity=quantity,
                trial_days=trial_days,
                metadata=metadata or {"price_id": str(price_id)}
            )
            
            # Create local subscription record
            subscription = Subscription(
                customer_id=customer_id,
                stripe_subscription_id=stripe_subscription["id"],
                status=stripe_subscription["status"],
                current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"]),
                metadata=metadata or {},
                is_auto_renew=True
            )
            
            # Add trial dates if applicable
            if stripe_subscription.get("trial_start"):
                subscription.trial_start = datetime.fromtimestamp(stripe_subscription["trial_start"])
                subscription.trial_end = datetime.fromtimestamp(stripe_subscription["trial_end"])
            
            # Save subscription
            created_subscription = await self.subscription_repository.create(subscription)
            
            # Create subscription items
            for item in stripe_subscription["items"]["data"]:
                subscription_item = SubscriptionItem(
                    subscription_id=created_subscription.id,
                    price_id=price_id,
                    stripe_subscription_item_id=item["id"],
                    quantity=item["quantity"],
                    metadata={}
                )
                
                await self.db.add(subscription_item)
            
            await self.db.commit()
            return created_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def update_subscription(
        self,
        subscription_id: int,
        **kwargs
    ) -> Subscription:
        """
        Update a subscription
        
        Args:
            subscription_id: Subscription ID
            **kwargs: Fields to update
            
        Returns:
            Updated subscription object
            
        Raises:
            ValueError: If subscription doesn't exist
        """
        # Get subscription
        subscription = await self.subscription_repository.get(
            subscription_id, 
            options=[selectinload(Subscription.items)]
        )
        
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
        
        # Fields for Stripe update
        stripe_update = {}
        
        # Fields for local update
        local_update = {}
        
        # Process update fields
        for key, value in kwargs.items():
            if key == "is_auto_renew":
                # Update cancel at period end in Stripe
                stripe_update["cancel_at_period_end"] = not value
                local_update["is_auto_renew"] = value
            elif key == "metadata":
                # Update both
                stripe_update["metadata"] = value
                local_update["metadata"] = value
            elif key in ["cancel_at", "trial_end"]:
                # Convert datetime to timestamp for Stripe
                if value:
                    stripe_update[key] = int(value.timestamp())
                else:
                    stripe_update[key] = None
                local_update[key] = value
            else:
                # Just update locally
                local_update[key] = value
        
        # Update in Stripe if needed
        if stripe_update:
            try:
                self.stripe_service.update_subscription(
                    subscription.stripe_subscription_id,
                    **stripe_update
                )
            except stripe.error.StripeError as e:
                logger.error(f"Failed to update Stripe subscription: {str(e)}")
                raise ValueError(f"Stripe error: {str(e)}")
        
        # Update locally
        if local_update:
            subscription = await self.subscription_repository.update(subscription_id, **local_update)
        
        return subscription
    
    async def cancel_subscription(
        self,
        subscription_id: int,
        at_period_end: bool = True
    ) -> Subscription:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Subscription ID
            at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            Updated subscription object
            
        Raises:
            ValueError: If subscription doesn't exist
        """
        # Get subscription
        subscription = await self.subscription_repository.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
        
        # Cancel in Stripe
        try:
            stripe_subscription = self.stripe_service.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=at_period_end
            )
            
            # Update status locally
            update_data = {
                "is_auto_renew": False
            }
            
            # If immediate cancellation, update status
            if not at_period_end:
                update_data["status"] = SubscriptionStatus.CANCELED
                
            # If Stripe provides canceled_at, use it
            if stripe_subscription.get("canceled_at"):
                update_data["canceled_at"] = datetime.fromtimestamp(stripe_subscription["canceled_at"])
                
            # Update subscription
            subscription = await self.subscription_repository.update(subscription_id, **update_data)
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe subscription: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """
        Get a subscription by Stripe subscription ID
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Subscription object or None if not found
        """
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def sync_subscription(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """
        Sync subscription data from Stripe
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Updated subscription object or None if not found
        """
        # Get subscription by Stripe ID
        subscription = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        
        # If not found, check if this is a new subscription
        if not subscription:
            # Try to create it if we have the customer
            try:
                # Get subscription from Stripe
                stripe_subscription = self.stripe_service.get_subscription(stripe_subscription_id)
                
                # Get customer by Stripe ID
                stripe_customer_id = stripe_subscription.get("customer")
                if not stripe_customer_id:
                    logger.error(f"Subscription {stripe_subscription_id} has no customer ID")
                    return None
                
                # Find customer
                customer = await self.customer_repository.get_by_stripe_id(stripe_customer_id)
                if not customer:
                    logger.error(f"Customer with Stripe ID {stripe_customer_id} not found")
                    return None
                
                # Create subscription record
                subscription = Subscription(
                    customer_id=customer.id,
                    stripe_subscription_id=stripe_subscription_id,
                    status=stripe_subscription["status"],
                    current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
                    current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"]),
                    metadata=stripe_subscription.get("metadata", {}),
                    is_auto_renew=not stripe_subscription.get("cancel_at_period_end", False)
                )
                
                # Add trial dates if applicable
                if stripe_subscription.get("trial_start"):
                    subscription.trial_start = datetime.fromtimestamp(stripe_subscription["trial_start"])
                    subscription.trial_end = datetime.fromtimestamp(stripe_subscription["trial_end"])
                
                # Add cancel dates if applicable
                if stripe_subscription.get("cancel_at"):
                    subscription.cancel_at = datetime.fromtimestamp(stripe_subscription["cancel_at"])
                
                if stripe_subscription.get("canceled_at"):
                    subscription.canceled_at = datetime.fromtimestamp(stripe_subscription["canceled_at"])
                
                # Save subscription
                created_subscription = await self.subscription_repository.create(subscription)
                
                # Create subscription items
                for item in stripe_subscription["items"]["data"]:
                    # Find price by Stripe ID
                    price_stmt = select(Price).where(Price.stripe_price_id == item["price"]["id"])
                    price_result = await self.db.execute(price_stmt)
                    price = price_result.scalars().first()
                    
                    if not price:
                        logger.warning(f"Price with Stripe ID {item['price']['id']} not found")
                        continue
                    
                    subscription_item = SubscriptionItem(
                        subscription_id=created_subscription.id,
                        price_id=price.id,
                        stripe_subscription_item_id=item["id"],
                        quantity=item["quantity"],
                        metadata={}
                    )
                    
                    self.db.add(subscription_item)
                
                await self.db.commit()
                return created_subscription
                
            except Exception as e:
                logger.error(f"Failed to create subscription from webhook: {str(e)}")
                return None
        
        # Update existing subscription
        try:
            # Get data from Stripe
            stripe_subscription = self.stripe_service.get_subscription(stripe_subscription_id)
            
            # Extract data
            update_data = {
                "status": stripe_subscription["status"],
                "current_period_start": datetime.fromtimestamp(stripe_subscription["current_period_start"]),
                "current_period_end": datetime.fromtimestamp(stripe_subscription["current_period_end"]),
                "metadata": stripe_subscription.get("metadata", {}),
                "is_auto_renew": not stripe_subscription.get("cancel_at_period_end", False)
            }
            
            # Add trial dates if applicable
            if stripe_subscription.get("trial_start"):
                update_data["trial_start"] = datetime.fromtimestamp(stripe_subscription["trial_start"])
                update_data["trial_end"] = datetime.fromtimestamp(stripe_subscription["trial_end"])
            
            # Add cancel dates if applicable
            if stripe_subscription.get("cancel_at"):
                update_data["cancel_at"] = datetime.fromtimestamp(stripe_subscription["cancel_at"])
            
            if stripe_subscription.get("canceled_at"):
                update_data["canceled_at"] = datetime.fromtimestamp(stripe_subscription["canceled_at"])
            
            # Update subscription
            subscription = await self.subscription_repository.update(subscription.id, **update_data)
            
            # TODO: Sync subscription items if needed
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync subscription from Stripe: {str(e)}")
            return subscription
    
    async def mark_subscription_deleted(self, stripe_subscription_id: str) -> bool:
        """
        Mark a subscription as deleted in our database after Stripe deletion
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Success flag
        """
        # Find subscription
        subscription = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        if not subscription:
            logger.warning(f"Subscription with Stripe ID {stripe_subscription_id} not found in database")
            return False
        
        # Mark as ended
        try:
            await self.subscription_repository.update(
                subscription.id,
                status=SubscriptionStatus.ENDED,
                canceled_at=datetime.now()
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark subscription as deleted: {str(e)}")
            return False
    
    async def handle_trial_ending(self, stripe_subscription_id: str) -> bool:
        """
        Handle trial ending soon notification
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Success flag
        """
        # Find subscription
        subscription = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        if not subscription:
            logger.warning(f"Subscription with Stripe ID {stripe_subscription_id} not found in database")
            return False
        
        # TODO: Send notification to customer about trial ending
        
        logger.info(f"Trial ending for subscription {subscription.id}")
        return True