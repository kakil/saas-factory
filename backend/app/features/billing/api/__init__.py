from fastapi import APIRouter

from app.features.billing.api.endpoints import plans, customers, subscriptions, invoices, payments, webhooks

router = APIRouter()

router.include_router(plans.router, prefix="/plans", tags=["plans"])
router.include_router(customers.router, prefix="/customers", tags=["customers"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])