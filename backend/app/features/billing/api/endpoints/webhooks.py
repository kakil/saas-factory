from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.features.billing.service.stripe_service import StripeService
from app.features.billing.service.webhook_service import WebhookService
from app.features.billing.service.subscription_service import SubscriptionService
from app.features.billing.service.invoice_service import InvoiceService
from app.features.billing.service.customer_service import CustomerService
from app.features.billing.service.payment_service import PaymentService
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.repository.subscription_repository import SubscriptionRepository
from app.features.billing.repository.invoice_repository import InvoiceRepository
from app.features.billing.repository.payment_repository import PaymentRepository

router = APIRouter()


@router.post(\"/stripe\")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    \"\"\"
    Handle Stripe webhook events
    
    This endpoint receives webhook events from Stripe and processes them
    to sync data between Stripe and our database.
    \"\"\"
    # Initialize services
    stripe_service = StripeService()
    customer_repository = CustomerRepository(db)
    subscription_repository = SubscriptionRepository(db)
    invoice_repository = InvoiceRepository(db)
    payment_repository = PaymentRepository(db)
    
    customer_service = CustomerService(db, stripe_service, customer_repository)
    subscription_service = SubscriptionService(db, stripe_service, subscription_repository, customer_repository)
    invoice_service = InvoiceService(db, stripe_service, invoice_repository, customer_repository)
    payment_service = PaymentService(db, stripe_service, payment_repository, customer_repository)
    
    webhook_service = WebhookService(
        stripe_service,
        subscription_service,
        invoice_service,
        payment_service,
        customer_service,
    )
    
    # Process webhook
    return await webhook_service.process_webhook(request, background_tasks)