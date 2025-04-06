from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_payment_service
from app.features.billing.service.payment_service import PaymentService
from app.features.billing.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse

router = APIRouter()


@router.post("", response_model=PaymentResponse)
async def create_payment(
    payment_in: PaymentCreate,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Create a new payment intent
    
    This endpoint creates a new payment intent for a customer.
    """
    try:
        payment = await payment_service.create_payment_intent(
            customer_id=payment_in.customer_id,
            amount=payment_in.amount,
            currency=payment_in.currency,
            payment_method_id=payment_in.payment_method_id,
            description=payment_in.description,
            metadata=payment_in.metadata,
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    customer_id: int = Query(..., description="Customer ID"),
    limit: int = Query(10, description="Maximum number of payments to return"),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    List payments for a customer
    
    This endpoint retrieves all payments for a customer.
    """
    payments = await payment_service.payment_repository.list_by_customer(
        customer_id=customer_id, limit=limit
    )
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Get a payment by ID
    
    This endpoint retrieves a payment by its ID.
    """
    payment = await payment_service.payment_repository.get(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found",
        )
    return payment


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    payment_method_id: str = Query(None, description="Payment method ID to use for confirmation"),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Confirm a payment intent
    
    This endpoint confirms a payment intent with an optional payment method.
    """
    try:
        payment = await payment_service.confirm_payment_intent(
            payment_id=payment_id,
            payment_method_id=payment_method_id,
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{payment_id}/capture", response_model=PaymentResponse)
async def capture_payment(
    payment_id: int,
    amount_to_capture: int = Query(None, description="Amount to capture in cents"),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Capture a payment intent
    
    This endpoint captures an authorized payment intent with an optional amount.
    """
    try:
        payment = await payment_service.capture_payment_intent(
            payment_id=payment_id,
            amount_to_capture=amount_to_capture,
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Cancel a payment intent
    
    This endpoint cancels a payment intent.
    """
    try:
        payment = await payment_service.cancel_payment_intent(payment_id)
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )