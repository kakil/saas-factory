from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.features.billing.service.stripe_service import StripeService
from app.features.billing.service.customer_service import CustomerService
from app.features.billing.service.plan_service import PlanService
from app.features.billing.service.subscription_service import SubscriptionService
from app.features.billing.service.invoice_service import InvoiceService
from app.features.billing.service.payment_service import PaymentService
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.repository.plan_repository import PlanRepository
from app.features.billing.repository.subscription_repository import SubscriptionRepository
from app.features.billing.repository.invoice_repository import InvoiceRepository
from app.features.billing.repository.payment_repository import PaymentRepository
from app.features.billing.repository.price_repository import PriceRepository


# Stripe service
def get_stripe_service() -> StripeService:
    return StripeService()


# Repositories
def get_customer_repository(db: AsyncSession = Depends(get_db)) -> CustomerRepository:
    return CustomerRepository(db)


def get_plan_repository(db: AsyncSession = Depends(get_db)) -> PlanRepository:
    return PlanRepository(db)


def get_subscription_repository(db: AsyncSession = Depends(get_db)) -> SubscriptionRepository:
    return SubscriptionRepository(db)


def get_invoice_repository(db: AsyncSession = Depends(get_db)) -> InvoiceRepository:
    return InvoiceRepository(db)


def get_payment_repository(db: AsyncSession = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(db)


def get_price_repository(db: AsyncSession = Depends(get_db)) -> PriceRepository:
    return PriceRepository(db)


# Services
def get_customer_service(
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    customer_repository: CustomerRepository = Depends(get_customer_repository),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    invoice_repository: InvoiceRepository = Depends(get_invoice_repository),
) -> CustomerService:
    service = CustomerService(db, stripe_service, customer_repository)
    # Add additional repositories as attributes
    service.subscription_repository = subscription_repository
    service.invoice_repository = invoice_repository
    return service


def get_plan_service(
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    plan_repository: PlanRepository = Depends(get_plan_repository),
) -> PlanService:
    return PlanService(db, stripe_service, plan_repository)


def get_subscription_service(
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    customer_repository: CustomerRepository = Depends(get_customer_repository),
    plan_repository: PlanRepository = Depends(get_plan_repository),
    price_repository: PriceRepository = Depends(get_price_repository),
) -> SubscriptionService:
    return SubscriptionService(
        db, 
        stripe_service, 
        subscription_repository, 
        customer_repository,
        plan_repository,
        price_repository
    )


def get_invoice_service(
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    invoice_repository: InvoiceRepository = Depends(get_invoice_repository),
    customer_repository: CustomerRepository = Depends(get_customer_repository),
) -> InvoiceService:
    return InvoiceService(db, stripe_service, invoice_repository, customer_repository)


def get_payment_service(
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    customer_repository: CustomerRepository = Depends(get_customer_repository),
) -> PaymentService:
    return PaymentService(db, stripe_service, payment_repository, customer_repository)