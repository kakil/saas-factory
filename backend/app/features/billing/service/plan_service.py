import logging
from typing import Any, Dict, List, Optional, Union

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.features.billing.models.plan import Plan, PlanInterval
from app.features.billing.models.price import Price, PriceCurrency, PriceType
from app.features.billing.repository.plan_repository import PlanRepository
from app.features.billing.service.stripe_service import StripeService

logger = logging.getLogger(__name__)


class PlanService:
    """
    Service for managing subscription plans
    Handles creation, updating, and pricing of plans
    """
    
    def __init__(self, db: AsyncSession, stripe_service: StripeService, plan_repository: PlanRepository):
        self.db = db
        self.stripe_service = stripe_service
        self.plan_repository = plan_repository
    
    async def create_plan(
        self,
        name: str,
        description: Optional[str] = None,
        features: Optional[List[str]] = None,
        is_public: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """
        Create a new subscription plan
        
        Args:
            name: Plan name
            description: Plan description (optional)
            features: List of features (optional)
            is_public: Whether the plan is publicly available
            metadata: Additional metadata (optional)
            
        Returns:
            Created plan object
        """
        # Create product in Stripe
        try:
            stripe_product = self.stripe_service.create_product(
                name=name,
                description=description,
                metadata=metadata or {}
            )
            
            # Create local plan
            plan = Plan(
                name=name,
                description=description,
                stripe_product_id=stripe_product["id"],
                is_active=True,
                is_public=is_public,
                features=features or [],
                metadata=metadata or {}
            )
            
            return await self.plan_repository.create(plan)
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe product: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def update_plan(
        self,
        plan_id: int,
        **kwargs
    ) -> Plan:
        """
        Update a plan
        
        Args:
            plan_id: Plan ID
            **kwargs: Fields to update
            
        Returns:
            Updated plan object
            
        Raises:
            ValueError: If plan doesn't exist
        """
        # Get plan
        plan = await self.plan_repository.get(plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
        
        # Fields to update in Stripe
        stripe_fields = {}
        
        # Fields to update locally
        local_fields = {}
        
        # Process kwargs
        for key, value in kwargs.items():
            if key in ["name", "description", "metadata"]:
                # Update in both places
                stripe_fields[key] = value
                local_fields[key] = value
            elif key in ["features", "is_public", "is_active"]:
                # Only update locally
                local_fields[key] = value
                
                # If activating/deactivating, also update in Stripe
                if key == "is_active":
                    stripe_fields["active"] = value
        
        # Update in Stripe
        if stripe_fields and plan.stripe_product_id:
            try:
                self.stripe_service.update_product(
                    plan.stripe_product_id,
                    **stripe_fields
                )
            except stripe.error.StripeError as e:
                logger.error(f"Failed to update Stripe product: {str(e)}")
                raise ValueError(f"Stripe error: {str(e)}")
        
        # Update locally
        if local_fields:
            plan = await self.plan_repository.update(plan_id, **local_fields)
        
        return plan
    
    async def add_price_to_plan(
        self,
        plan_id: int,
        amount: int,  # Amount in cents
        currency: str = PriceCurrency.USD,
        interval: Optional[str] = PlanInterval.MONTHLY,
        price_type: str = PriceType.RECURRING,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Price:
        """
        Add a price to a plan
        
        Args:
            plan_id: Plan ID
            amount: Price amount in cents (e.g., 1000 for $10.00)
            currency: Currency code (default: USD)
            interval: Billing interval (default: MONTHLY, can be None for one-time)
            price_type: Price type (default: RECURRING)
            metadata: Additional metadata (optional)
            
        Returns:
            Created price object
            
        Raises:
            ValueError: If plan doesn't exist
        """
        # Get plan
        plan = await self.plan_repository.get(plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
        
        # Validate interval
        if price_type == PriceType.RECURRING and not interval:
            raise ValueError("Interval must be specified for recurring prices")
        
        # Create price in Stripe
        try:
            stripe_price = self.stripe_service.create_price(
                product_id=plan.stripe_product_id,
                amount=amount,
                currency=currency,
                interval=interval,
                metadata=metadata or {}
            )
            
            # Create local price
            price = Price(
                plan_id=plan_id,
                stripe_price_id=stripe_price["id"],
                amount=amount / 100.0,  # Convert from cents to dollars
                currency=currency,
                interval=interval,
                price_type=price_type,
                is_active=True,
                metadata=metadata or {}
            )
            
            # Add to database
            self.db.add(price)
            await self.db.commit()
            await self.db.refresh(price)
            
            return price
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe price: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def get_plan_with_prices(self, plan_id: int) -> Optional[Plan]:
        """
        Get a plan with its prices
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan object with prices or None if not found
        """
        stmt = select(Plan).where(Plan.id == plan_id).options(selectinload(Plan.prices))
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_plans(self, active_only: bool = True, public_only: bool = True) -> List[Plan]:
        """
        List available plans
        
        Args:
            active_only: Whether to only include active plans
            public_only: Whether to only include public plans
            
        Returns:
            List of plans
        """
        # Base query
        stmt = select(Plan).options(selectinload(Plan.prices))
        
        # Apply filters
        if active_only:
            stmt = stmt.where(Plan.is_active == True)
            
        if public_only:
            stmt = stmt.where(Plan.is_public == True)
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())