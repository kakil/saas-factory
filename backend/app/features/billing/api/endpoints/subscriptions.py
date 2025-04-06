from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_subscription_service
from app.features.billing.service.subscription_service import SubscriptionService
from app.features.billing.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse

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