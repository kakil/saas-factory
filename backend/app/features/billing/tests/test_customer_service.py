import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.billing.service.customer_service import CustomerService
from app.features.billing.service.stripe_service import StripeService
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.models.customer import Customer, CustomerTier
from app.features.teams.models import Organization


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_stripe_service():
    return MagicMock(spec=StripeService)


@pytest.fixture
def mock_customer_repository():
    return AsyncMock(spec=CustomerRepository)


@pytest.fixture
def customer_service(mock_db, mock_stripe_service, mock_customer_repository):
    return CustomerService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        customer_repository=mock_customer_repository
    )


class TestCustomerService:
    """Tests for the CustomerService class"""

    @pytest.mark.asyncio
    async def test_get_or_create_customer_existing(
        self, customer_service, mock_customer_repository
    ):
        # Setup mocks
        organization_id = 1
        existing_customer = Customer(
            id=1,
            organization_id=organization_id,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.FREE
        )
        mock_customer_repository.get_by_organization_id.return_value = existing_customer

        # Call the function
        result = await customer_service.get_or_create_customer(organization_id)

        # Assert
        mock_customer_repository.get_by_organization_id.assert_called_once_with(organization_id)
        assert result == existing_customer
        customer_service.stripe_service.create_customer.assert_not_called()
        mock_customer_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_customer_new(
        self, customer_service, mock_db, mock_customer_repository, mock_stripe_service
    ):
        # Setup mocks
        organization_id = 1
        mock_customer_repository.get_by_organization_id.return_value = None

        # Mock SQLAlchemy query result
        mock_organization = Organization(
            id=organization_id,
            name="Test Organization"
        )
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_organization.members = [mock_user]

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_organization
        mock_db.execute.return_value = mock_result

        # Mock Stripe response
        stripe_customer = {
            "id": "cus_123456789",
            "email": "test@example.com",
            "name": "Test Organization",
            "metadata": {"organization_id": "1"}
        }
        mock_stripe_service.create_customer.return_value = stripe_customer

        # Mock created customer
        created_customer = Customer(
            id=1,
            organization_id=organization_id,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.FREE
        )
        mock_customer_repository.create.return_value = created_customer

        # Call the function
        result = await customer_service.get_or_create_customer(organization_id)

        # Assert
        mock_customer_repository.get_by_organization_id.assert_called_once_with(organization_id)
        mock_stripe_service.create_customer.assert_called_once_with(
            email="test@example.com",
            name="Test Organization",
            metadata={"organization_id": "1"}
        )
        assert mock_customer_repository.create.call_count == 1
        assert result == created_customer

    @pytest.mark.asyncio
    async def test_update_customer(
        self, customer_service, mock_customer_repository, mock_stripe_service
    ):
        # Setup mocks
        customer_id = 1
        existing_customer = Customer(
            id=customer_id,
            organization_id=1,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.FREE,
            billing_email="old@example.com"
        )
        mock_customer_repository.get.return_value = existing_customer

        updated_customer = Customer(
            id=customer_id,
            organization_id=1,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.STANDARD,
            billing_email="new@example.com"
        )
        mock_customer_repository.update.return_value = updated_customer

        # Call the function
        result = await customer_service.update_customer(
            customer_id,
            tier=CustomerTier.STANDARD,
            billing_email="new@example.com"
        )

        # Assert
        mock_customer_repository.get.assert_called_once_with(customer_id)
        mock_stripe_service.update_customer.assert_called_once_with(
            "cus_123456789",
            email="new@example.com"
        )
        mock_customer_repository.update.assert_called_once_with(
            customer_id,
            tier=CustomerTier.STANDARD,
            billing_email="new@example.com"
        )
        assert result == updated_customer

    @pytest.mark.asyncio
    async def test_update_customer_not_found(
        self, customer_service, mock_customer_repository
    ):
        # Setup mocks
        customer_id = 999
        mock_customer_repository.get.return_value = None

        # Call the function and assert
        with pytest.raises(ValueError) as exc_info:
            await customer_service.update_customer(
                customer_id,
                tier=CustomerTier.STANDARD
            )

        assert f"Customer with ID {customer_id} not found" in str(exc_info.value)
        mock_customer_repository.get.assert_called_once_with(customer_id)
        customer_service.stripe_service.update_customer.assert_not_called()
        mock_customer_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_customer(
        self, customer_service, mock_customer_repository, mock_stripe_service
    ):
        # Setup mocks
        stripe_customer_id = "cus_123456789"
        existing_customer = Customer(
            id=1,
            organization_id=1,
            stripe_customer_id=stripe_customer_id,
            tier=CustomerTier.FREE
        )
        mock_customer_repository.get_by_stripe_id.return_value = existing_customer

        # Mock Stripe response
        stripe_customer = {
            "id": stripe_customer_id,
            "email": "test@example.com",
            "name": "Test Customer",
            "tax_exempt": "none",
            "metadata": {"key": "value"},
            "invoice_settings": {"default_payment_method": "pm_123456789"}
        }
        mock_stripe_service.get_customer.return_value = stripe_customer

        updated_customer = Customer(
            id=1,
            organization_id=1,
            stripe_customer_id=stripe_customer_id,
            tier=CustomerTier.FREE,
            billing_email="test@example.com",
            billing_name="Test Customer",
            default_payment_method_id="pm_123456789"
        )
        mock_customer_repository.update.return_value = updated_customer

        # Call the function
        result = await customer_service.sync_customer(stripe_customer_id)

        # Assert
        mock_customer_repository.get_by_stripe_id.assert_called_once_with(stripe_customer_id)
        mock_stripe_service.get_customer.assert_called_once_with(stripe_customer_id)
        mock_customer_repository.update.assert_called_once_with(
            1,
            billing_email="test@example.com",
            billing_name="Test Customer",
            tax_exempt="none",
            metadata={"key": "value"},
            default_payment_method_id="pm_123456789"
        )
        assert result == updated_customer