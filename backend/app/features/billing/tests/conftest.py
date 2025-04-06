import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.db.session import get_db
from app.features.billing.dependencies import (
    get_stripe_service,
    get_customer_repository,
    get_plan_repository,
    get_subscription_repository,
    get_invoice_repository,
    get_payment_repository,
    get_customer_service,
    get_plan_service,
    get_subscription_service,
    get_invoice_service,
    get_payment_service,
)
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
from app.features.billing.models.customer import Customer, CustomerTier
from app.features.billing.models.plan import Plan, PlanInterval
from app.features.billing.models.price import Price, PriceCurrency, PriceType
from app.features.billing.models.subscription import Subscription, SubscriptionStatus, SubscriptionItem
from app.features.billing.models.invoice import Invoice, InvoiceStatus, InvoiceItem
from app.features.billing.models.payment import Payment, PaymentStatus, PaymentMethod


@pytest.fixture
def mock_db():
    """Return a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_stripe_service():
    """Return a mock Stripe service."""
    return MagicMock(spec=StripeService)


@pytest.fixture
def mock_customer_repository():
    """Return a mock customer repository."""
    return AsyncMock(spec=CustomerRepository)


@pytest.fixture
def mock_plan_repository():
    """Return a mock plan repository."""
    return AsyncMock(spec=PlanRepository)


@pytest.fixture
def mock_subscription_repository():
    """Return a mock subscription repository."""
    return AsyncMock(spec=SubscriptionRepository)


@pytest.fixture
def mock_invoice_repository():
    """Return a mock invoice repository."""
    return AsyncMock(spec=InvoiceRepository)


@pytest.fixture
def mock_payment_repository():
    """Return a mock payment repository."""
    return AsyncMock(spec=PaymentRepository)


@pytest.fixture
def mock_customer_service(mock_db, mock_stripe_service, mock_customer_repository):
    """Return a mock customer service."""
    return CustomerService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        customer_repository=mock_customer_repository
    )


@pytest.fixture
def mock_plan_service(mock_db, mock_stripe_service, mock_plan_repository):
    """Return a mock plan service."""
    return PlanService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        plan_repository=mock_plan_repository
    )


@pytest.fixture
def mock_subscription_service(
    mock_db, mock_stripe_service, mock_subscription_repository, mock_customer_repository
):
    """Return a mock subscription service."""
    return SubscriptionService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        subscription_repository=mock_subscription_repository,
        customer_repository=mock_customer_repository
    )


@pytest.fixture
def mock_invoice_service(
    mock_db, mock_stripe_service, mock_invoice_repository, mock_customer_repository
):
    """Return a mock invoice service."""
    return InvoiceService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        invoice_repository=mock_invoice_repository,
        customer_repository=mock_customer_repository
    )


@pytest.fixture
def mock_payment_service(
    mock_db, mock_stripe_service, mock_payment_repository, mock_customer_repository
):
    """Return a mock payment service."""
    return PaymentService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        payment_repository=mock_payment_repository,
        customer_repository=mock_customer_repository
    )


@pytest.fixture
def client(
    mock_db,
    mock_stripe_service,
    mock_customer_service,
    mock_plan_service,
    mock_subscription_service,
    mock_invoice_service,
    mock_payment_service
):
    """Return a FastAPI test client with mocked dependencies."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_stripe_service] = lambda: mock_stripe_service
    app.dependency_overrides[get_customer_service] = lambda: mock_customer_service
    app.dependency_overrides[get_plan_service] = lambda: mock_plan_service
    app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service
    app.dependency_overrides[get_invoice_service] = lambda: mock_invoice_service
    app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
    
    # Return test client
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_customer():
    """Return a sample customer for testing."""
    return Customer(
        id=1,
        organization_id=1,
        stripe_customer_id="cus_123456789",
        tier=CustomerTier.STANDARD,
        billing_email="test@example.com",
        billing_name="Test Customer",
        default_payment_method_id="pm_123456789",
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_plan():
    """Return a sample plan for testing."""
    return Plan(
        id=1,
        name="Standard Plan",
        description="Standard Plan with all features",
        stripe_product_id="prod_123456789",
        is_active=True,
        is_public=True,
        features=["feature1", "feature2"],
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_price():
    """Return a sample price for testing."""
    return Price(
        id=1,
        plan_id=1,
        stripe_price_id="price_123456789",
        amount=29.99,
        currency=PriceCurrency.USD,
        interval=PlanInterval.MONTHLY,
        price_type=PriceType.RECURRING,
        is_active=True,
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_subscription():
    """Return a sample subscription for testing."""
    return Subscription(
        id=1,
        customer_id=1,
        stripe_subscription_id="sub_123456789",
        status=SubscriptionStatus.ACTIVE,
        current_period_start=None,
        current_period_end=None,
        is_auto_renew=True,
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_invoice():
    """Return a sample invoice for testing."""
    return Invoice(
        id=1,
        customer_id=1,
        subscription_id=1,
        stripe_invoice_id="in_123456789",
        status=InvoiceStatus.PAID,
        currency=PriceCurrency.USD,
        subtotal=29.99,
        tax=0,
        total=29.99,
        paid=True,
        amount_paid=29.99,
        amount_due=0,
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_payment():
    """Return a sample payment for testing."""
    return Payment(
        id=1,
        customer_id=1,
        invoice_id=1,
        stripe_payment_intent_id="pi_123456789",
        stripe_payment_method_id="pm_123456789",
        amount=29.99,
        currency=PriceCurrency.USD,
        status=PaymentStatus.SUCCEEDED,
        payment_method=PaymentMethod.CARD,
        metadata={"key": "value"}
    )