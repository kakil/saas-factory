import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.db.session import get_db
from app.features.billing.models.subscription import Subscription, SubscriptionItem, SubscriptionStatus
from app.features.billing.models.customer import Customer, CustomerTier
from app.features.billing.models.price import Price
from app.features.billing.models.plan import Plan
from app.features.billing.repository.subscription_repository import SubscriptionRepository
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.repository.plan_repository import PlanRepository
from app.features.billing.repository.price_repository import PriceRepository
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
        customer_repository: CustomerRepository,
        plan_repository: PlanRepository,
        price_repository: PriceRepository
    ):
        self.db = db
        self.stripe_service = stripe_service
        self.subscription_repository = subscription_repository
        self.customer_repository = customer_repository
        self.plan_repository = plan_repository
        self.price_repository = price_repository
    
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
        
    async def upgrade_subscription(
        self,
        subscription_id: int,
        plan_id: int,
        effective_date: Optional[datetime] = None,
        prorate: bool = True,
        maintain_trial: bool = True
    ) -> Subscription:
        """
        Upgrade or downgrade a subscription to a different plan
        
        Args:
            subscription_id: ID of the subscription to upgrade
            plan_id: ID of the new plan
            effective_date: When the change should take effect (default: immediate)
            prorate: Whether to prorate charges for the remainder of the billing period
            maintain_trial: Whether to maintain the trial period if applicable
            
        Returns:
            Updated subscription
            
        Raises:
            ValueError: If subscription or plan doesn't exist
        """
        # Get subscription with items
        subscription = await self.subscription_repository.get_with_items(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
            
        # Get plan
        plan = await self.plan_repository.get(plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
            
        # Get default price for the plan
        stmt = select(Price).where(Price.plan_id == plan_id, Price.is_active == True)
        result = await self.db.execute(stmt)
        price = result.scalars().first()
        
        if not price:
            raise ValueError(f"No active price found for plan with ID {plan_id}")
            
        # Get current subscription item - assuming there's only one
        if not subscription.items or len(subscription.items) == 0:
            raise ValueError(f"Subscription {subscription_id} has no items")
            
        current_item = subscription.items[0]
            
        try:
            # Determine effective date timestamp
            effective_timestamp = None
            if effective_date:
                effective_timestamp = int(effective_date.timestamp())
                
            # For Stripe, create an item replacement
            stripe_updates = {
                "items": [
                    {
                        "id": current_item.stripe_subscription_item_id, 
                        "deleted": True
                    },
                    {
                        "price": price.stripe_price_id,
                        "quantity": current_item.quantity
                    }
                ],
                "proration_behavior": "create_prorations" if prorate else "none",
            }
            
            # If effective date is provided, use it
            if effective_timestamp:
                stripe_updates["proration_date"] = effective_timestamp
                
            # If maintaining trial, add it to the updates
            if maintain_trial and subscription.trial_end:
                stripe_updates["trial_end"] = int(subscription.trial_end.timestamp())
                
            # Update subscription in Stripe
            stripe_subscription = self.stripe_service.update_subscription(
                subscription.stripe_subscription_id,
                **stripe_updates
            )
            
            # Update subscription items in our database
            # First mark the existing item as deleted
            await self.db.execute(
                update(SubscriptionItem)
                .where(SubscriptionItem.id == current_item.id)
                .values(updated_at=datetime.now())
            )
            
            # Create new item from Stripe response
            for item in stripe_subscription["items"]["data"]:
                if not item.get("deleted", False):
                    # This is the new item
                    new_item = SubscriptionItem(
                        subscription_id=subscription.id,
                        price_id=price.id,
                        stripe_subscription_item_id=item["id"],
                        quantity=item["quantity"],
                        metadata={}
                    )
                    
                    self.db.add(new_item)
            
            # Update customer tier based on plan
            customer = await self.customer_repository.get(subscription.customer_id)
            if customer and plan.tier != customer.tier:
                await self.customer_repository.update(customer.id, tier=plan.tier)
                
            # Sync subscription from Stripe to update status and dates
            updated_subscription = await self.sync_subscription(subscription.stripe_subscription_id)
            
            await self.db.commit()
            return updated_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to upgrade subscription in Stripe: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
            
    async def schedule_subscription_update(
        self,
        subscription_id: int,
        plan_id: int,
        scheduled_date: datetime,
        prorate: bool = True
    ) -> Dict[str, Any]:
        """
        Schedule a subscription update for a future date
        
        Args:
            subscription_id: ID of the subscription to update
            plan_id: ID of the new plan
            scheduled_date: When the change should take effect
            prorate: Whether to prorate charges
            
        Returns:
            Scheduled update information
            
        Raises:
            ValueError: If subscription or plan doesn't exist
        """
        # Get subscription
        subscription = await self.subscription_repository.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
            
        # Get plan
        plan = await self.plan_repository.get(plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
            
        # Get default price for the plan
        stmt = select(Price).where(Price.plan_id == plan_id, Price.is_active == True)
        result = await self.db.execute(stmt)
        price = result.scalars().first()
        
        if not price:
            raise ValueError(f"No active price found for plan with ID {plan_id}")
            
        try:
            # Schedule update in Stripe
            scheduled_update = self.stripe_service.create_subscription_schedule(
                stripe_subscription_id=subscription.stripe_subscription_id,
                start_date=int(scheduled_date.timestamp()),
                price_id=price.stripe_price_id,
                proration_behavior="create_prorations" if prorate else "none"
            )
            
            # Store the schedule info in subscription metadata
            metadata = subscription.metadata or {}
            metadata["scheduled_update"] = {
                "schedule_id": scheduled_update.get("id"),
                "plan_id": plan_id,
                "price_id": price.id,
                "scheduled_date": scheduled_date.isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            await self.subscription_repository.update(
                subscription_id,
                metadata=metadata
            )
            
            return {
                "subscription_id": subscription_id,
                "plan_id": plan_id,
                "scheduled_date": scheduled_date,
                "schedule_id": scheduled_update.get("id")
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to schedule subscription update in Stripe: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
            
    async def handle_subscription_renewing(self, stripe_subscription_id: str) -> bool:
        """
        Handle subscription renewing soon notification
        
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
            
        # Get customer
        customer = await self.customer_repository.get(subscription.customer_id)
        if not customer:
            logger.warning(f"Customer for subscription {subscription_id} not found")
            return False
            
        # TODO: Send notification to customer about upcoming renewal
        
        # Get subscription item details
        if not subscription.items or len(subscription.items) == 0:
            logger.warning(f"Subscription {subscription.id} has no items")
            return False
            
        item = subscription.items[0]
        price = await self.price_repository.get(item.price_id)
        if not price:
            logger.warning(f"Price for subscription item {item.id} not found")
            return False
            
        renewal_date = subscription.current_period_end
        renewal_amount = price.amount * item.quantity
            
        logger.info(f"Subscription {subscription.id} renewing on {renewal_date} for {renewal_amount}")
        return True
        
    async def handle_payment_failed(self, stripe_subscription_id: str) -> bool:
        """
        Handle payment failed event for a subscription
        
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
            
        # Get latest status from Stripe
        try:
            stripe_subscription = self.stripe_service.get_subscription(stripe_subscription_id)
            
            # Update subscription status
            await self.subscription_repository.update(
                subscription.id,
                status=stripe_subscription["status"]
            )
            
            # If past_due, send notification to customer
            if stripe_subscription["status"] == SubscriptionStatus.PAST_DUE:
                # TODO: Send payment failed notification
                pass
                
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription from Stripe: {str(e)}")
            return False
            
    async def reactivate_subscription(self, subscription_id: int) -> Subscription:
        """
        Reactivate a canceled subscription that is still within its period
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Reactivated subscription
            
        Raises:
            ValueError: If subscription doesn't exist or can't be reactivated
        """
        # Get subscription
        subscription = await self.subscription_repository.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
            
        # Check if subscription can be reactivated
        if subscription.status != SubscriptionStatus.CANCELED:
            raise ValueError(f"Subscription is not canceled, current status: {subscription.status}")
            
        # Check if still within period
        if subscription.current_period_end and subscription.current_period_end < datetime.now():
            raise ValueError("Subscription period has already ended, cannot reactivate")
            
        try:
            # Reactivate in Stripe
            stripe_subscription = self.stripe_service.update_subscription(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            # Update local subscription
            update_data = {
                "status": stripe_subscription["status"],
                "is_auto_renew": True,
                "canceled_at": None
            }
            
            updated_subscription = await self.subscription_repository.update(
                subscription_id,
                **update_data
            )
            
            return updated_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to reactivate subscription in Stripe: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
            
    async def apply_coupon_to_subscription(
        self,
        subscription_id: int,
        coupon_code: str
    ) -> Subscription:
        """
        Apply a coupon to an existing subscription
        
        Args:
            subscription_id: Subscription ID
            coupon_code: Coupon code to apply
            
        Returns:
            Updated subscription
            
        Raises:
            ValueError: If subscription doesn't exist or coupon is invalid
        """
        # Get subscription
        subscription = await self.subscription_repository.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")
            
        try:
            # Apply coupon in Stripe
            stripe_subscription = self.stripe_service.update_subscription(
                subscription.stripe_subscription_id,
                coupon=coupon_code
            )
            
            # Sync subscription from Stripe
            updated_subscription = await self.sync_subscription(subscription.stripe_subscription_id)
            
            # Add coupon info to metadata
            metadata = updated_subscription.metadata or {}
            metadata["applied_coupon"] = {
                "code": coupon_code,
                "applied_at": datetime.now().isoformat()
            }
            
            updated_subscription = await self.subscription_repository.update(
                subscription_id,
                metadata=metadata
            )
            
            return updated_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to apply coupon to subscription in Stripe: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")