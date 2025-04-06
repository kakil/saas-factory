from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_customer_service
from app.features.billing.service.customer_service import CustomerService
from app.features.billing.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter()


@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer_in: CustomerCreate,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Create a new customer
    
    This endpoint creates a new billing customer for an organization.
    A customer is required for billing operations.
    """
    try:
        customer = await customer_service.get_or_create_customer(customer_in.organization_id)
        return customer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Get a customer by ID
    
    This endpoint retrieves a customer's billing information.
    """
    customer = await customer_service.customer_repository.get(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )
    return customer


@router.get("/organization/{organization_id}", response_model=CustomerResponse)
async def get_customer_by_organization(
    organization_id: int,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Get a customer by organization ID
    
    This endpoint retrieves a customer's billing information by organization ID.
    """
    customer = await customer_service.customer_repository.get_by_organization_id(organization_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer for organization with ID {organization_id} not found",
        )
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Update a customer
    
    This endpoint updates a customer's billing information.
    """
    try:
        customer = await customer_service.update_customer(
            customer_id, **customer_in.model_dump(exclude_unset=True)
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found",
            )
        return customer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )