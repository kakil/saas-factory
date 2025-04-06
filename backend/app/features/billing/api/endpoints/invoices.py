from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.api.responses import success_response
from app.features.billing.dependencies import get_invoice_service
from app.features.billing.service.invoice_service import InvoiceService
from app.features.billing.schemas.invoice import InvoiceResponse

router = APIRouter()


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    customer_id: int = Query(..., description="Customer ID"),
    paid_only: bool = Query(False, description="Whether to only include paid invoices"),
    limit: int = Query(10, description="Maximum number of invoices to return"),
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    """
    List invoices for a customer
    
    This endpoint retrieves all invoices for a customer, optionally filtered by paid status.
    """
    invoices = await invoice_service.invoice_repository.list_by_customer(
        customer_id=customer_id, paid_only=paid_only, limit=limit
    )
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    """
    Get an invoice by ID
    
    This endpoint retrieves an invoice by its ID.
    """
    invoice = await invoice_service.invoice_repository.get_with_items(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )
    return invoice