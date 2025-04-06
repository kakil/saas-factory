from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_customer_service
from app.features.billing.service.customer_service import CustomerService
from app.features.billing.models.customer import CustomerTier
from app.features.billing.schemas.customer import CustomerUpdate, OrganizationBillingResponse

router = APIRouter()


@router.get("/{organization_id}/billing", response_model=Dict[str, Any])
async def get_organization_billing(
    organization_id: int = Path(..., description="Organization ID"),
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Get billing information for an organization
    
    This endpoint retrieves comprehensive billing information for an organization,
    including customer details, subscription status, payment methods, and recent invoices.
    """
    try:
        billing_info = await customer_service.get_organization_billing_info(organization_id)
        return billing_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{organization_id}/billing", response_model=Dict[str, Any])
async def update_organization_billing(
    update_data: CustomerUpdate,
    organization_id: int = Path(..., description="Organization ID"),
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Update billing information for an organization
    
    This endpoint updates billing information for an organization's customer record.
    """
    try:
        # Get customer for organization
        customer = await customer_service.customer_repository.get_by_organization_id(organization_id)
        if not customer:
            raise ValueError(f"No customer record found for organization {organization_id}")
            
        # Update customer
        updated_customer = await customer_service.update_customer(
            customer.id, **update_data.model_dump(exclude_unset=True)
        )
        
        # Get full billing info
        billing_info = await customer_service.get_organization_billing_info(organization_id)
        
        return billing_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{organization_id}/tier", response_model=Dict[str, Any])
async def update_organization_tier(
    organization_id: int = Path(..., description="Organization ID"),
    tier: CustomerTier = None,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """
    Update the billing tier for an organization
    
    This endpoint updates the billing tier for an organization.
    """
    try:
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tier must be provided",
            )
            
        # Update tier
        await customer_service.update_organization_billing_tier(organization_id, tier)
        
        # Get full billing info
        billing_info = await customer_service.get_organization_billing_info(organization_id)
        
        return billing_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )