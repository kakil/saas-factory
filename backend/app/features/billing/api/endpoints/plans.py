from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_plan_service
from app.features.billing.service.plan_service import PlanService
from app.features.billing.schemas.plan import PlanCreate, PlanUpdate, PlanResponse, PriceCreate, PriceResponse

router = APIRouter()


@router.post("", response_model=PlanResponse)
async def create_plan(
    plan_in: PlanCreate,
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Create a new subscription plan
    
    This endpoint creates a new subscription plan with the given details.
    """
    try:
        plan = await plan_service.create_plan(
            name=plan_in.name,
            description=plan_in.description,
            features=plan_in.features,
            is_public=plan_in.is_public,
            metadata=plan_in.metadata,
        )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    active_only: bool = Query(True, description="Whether to only include active plans"),
    public_only: bool = Query(True, description="Whether to only include public plans"),
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    List subscription plans
    
    This endpoint retrieves all subscription plans, optionally filtered by active and public status.
    """
    plans = await plan_service.list_plans(active_only=active_only, public_only=public_only)
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Get a subscription plan by ID
    
    This endpoint retrieves a subscription plan by its ID.
    """
    plan = await plan_service.get_plan_with_prices(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_in: PlanUpdate,
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Update a subscription plan
    
    This endpoint updates a subscription plan with the given details.
    """
    try:
        plan = await plan_service.update_plan(
            plan_id, **plan_in.model_dump(exclude_unset=True)
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan with ID {plan_id} not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{plan_id}/prices", response_model=PriceResponse)
async def add_price_to_plan(
    plan_id: int,
    price_in: PriceCreate,
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Add a price to a subscription plan
    
    This endpoint adds a new price to an existing subscription plan.
    """
    try:
        price = await plan_service.add_price_to_plan(
            plan_id=plan_id,
            amount=int(price_in.amount * 100),  # Convert to cents
            currency=price_in.currency,
            interval=price_in.interval,
            price_type=price_in.price_type,
            metadata=price_in.metadata,
        )
        return price
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )