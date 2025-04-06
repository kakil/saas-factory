from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_subscription_service
from app.features.billing.service.subscription_service import SubscriptionService
from app.features.billing.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionUpdate, 
    SubscriptionResponse, 
    SubscriptionUpgrade,
    SubscriptionSchedule,
    CouponApply
)

router = APIRouter()


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_in: SubscriptionCreate,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Create a new subscription
    
    This endpoint creates a new subscription for a customer.
    """
    try:
        subscription = await subscription_service.create_subscription(
            customer_id=subscription_in.customer_id,
            price_id=subscription_in.price_id,
            quantity=subscription_in.quantity,
            trial_days=subscription_in.trial_days,
            metadata=subscription_in.metadata,
        )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    customer_id: int = Query(..., description="Customer ID"),
    active_only: bool = Query(True, description="Whether to only include active subscriptions"),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    List subscriptions for a customer
    
    This endpoint retrieves all subscriptions for a customer, optionally filtered by active status.
    """
    subscriptions = await subscription_service.subscription_repository.list_by_customer(
        customer_id=customer_id, active_only=active_only
    )
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Get a subscription by ID
    
    This endpoint retrieves a subscription by its ID.
    """
    subscription = await subscription_service.subscription_repository.get_with_items(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found",
        )
    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_in: SubscriptionUpdate,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Update a subscription
    
    This endpoint updates a subscription with the given details.
    """
    try:
        subscription = await subscription_service.update_subscription(
            subscription_id, **subscription_in.model_dump(exclude_unset=True)
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {subscription_id} not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    at_period_end: bool = Query(True, description="Whether to cancel at period end or immediately"),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Cancel a subscription
    
    This endpoint cancels a subscription, either at the end of the current period or immediately.
    """
    try:
        subscription = await subscription_service.cancel_subscription(
            subscription_id, at_period_end=at_period_end
        )
        return success_response(
            message=f"Subscription canceled {'at period end' if at_period_end else 'immediately'}",
            data={"subscription_id": subscription_id, "status": subscription.status}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{subscription_id}/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    subscription_id: int,
    upgrade_data: SubscriptionUpgrade,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Upgrade or downgrade a subscription
    
    This endpoint changes the plan for a subscription, either immediately or at a specified date.
    Proration can be enabled or disabled.
    """
    try:
        subscription = await subscription_service.upgrade_subscription(
            subscription_id=subscription_id,
            plan_id=upgrade_data.plan_id,
            effective_date=upgrade_data.effective_date,
            prorate=upgrade_data.prorate,
            maintain_trial=upgrade_data.maintain_trial
        )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{subscription_id}/schedule", response_model=Dict[str, Any])
async def schedule_subscription_update(
    subscription_id: int,
    schedule_data: SubscriptionSchedule,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Schedule a future subscription update
    
    This endpoint schedules a plan change for a future date.
    """
    try:
        schedule = await subscription_service.schedule_subscription_update(
            subscription_id=subscription_id,
            plan_id=schedule_data.plan_id,
            scheduled_date=schedule_data.scheduled_date,
            prorate=schedule_data.prorate
        )
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{subscription_id}/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Reactivate a canceled subscription
    
    This endpoint reactivates a previously canceled subscription, 
    as long as it's still within the current billing period.
    """
    try:
        subscription = await subscription_service.reactivate_subscription(subscription_id)
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{subscription_id}/apply-coupon", response_model=SubscriptionResponse)
async def apply_coupon(
    subscription_id: int,
    coupon_data: CouponApply,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Apply a coupon to a subscription
    
    This endpoint applies a coupon code to an existing subscription.
    """
    try:
        subscription = await subscription_service.apply_coupon_to_subscription(
            subscription_id=subscription_id,
            coupon_code=coupon_data.coupon_code
        )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )