import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import stripe
from datetime import datetime

from app.features.billing.service.payment_service import PaymentService
from app.features.billing.service.stripe_service import StripeService
from app.features.billing.repository.payment_repository import PaymentRepository
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.models.payment import Payment, PaymentStatus, PaymentMethod
from app.features.billing.models.customer import Customer, CustomerTier


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_stripe_service():
    return MagicMock(spec=StripeService)


@pytest.fixture
def mock_payment_repository():
    return AsyncMock(spec=PaymentRepository)


@pytest.fixture
def mock_customer_repository():
    return AsyncMock(spec=CustomerRepository)


@pytest.fixture
def payment_service(mock_db, mock_stripe_service, mock_payment_repository, mock_customer_repository):
    return PaymentService(
        db=mock_db,
        stripe_service=mock_stripe_service,
        payment_repository=mock_payment_repository,
        customer_repository=mock_customer_repository
    )


class TestPaymentWorkflow:
    """Tests for the payment workflow"""

    @pytest.mark.asyncio
    async def test_create_payment_intent_flow(
        self, payment_service, mock_customer_repository, mock_stripe_service, mock_payment_repository
    ):
        """
        Test the complete payment intent flow:
        1. Create payment intent
        2. Confirm payment intent
        3. Capture payment intent
        """
        # Setup mocks
        customer_id = 1
        customer = Customer(
            id=customer_id,
            organization_id=1,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.STANDARD
        )
        mock_customer_repository.get.return_value = customer

        # Mock stripe payment intent creation
        mock_payment_intent = {
            "id": "pi_123456789",
            "amount": 1000,
            "currency": "usd",
            "customer": "cus_123456789",
            "status": "requires_payment_method"
        }
        mock_stripe_service.create_payment_intent.return_value = mock_payment_intent

        # Mock payment repository creation
        payment_id = 1
        created_payment = Payment(
            id=payment_id,
            customer_id=customer_id,
            stripe_payment_intent_id="pi_123456789",
            amount=10.0,
            currency="usd",
            status=PaymentStatus.REQUIRES_PAYMENT_METHOD
        )
        mock_payment_repository.create.return_value = created_payment

        # Step 1: Create payment intent
        payment = await payment_service.create_payment_intent(
            customer_id=customer_id,
            amount=1000,  # $10.00
            currency="usd",
            payment_method_id=None,
            description="Test payment"
        )

        # Assert creation
        assert payment.id == payment_id
        assert payment.stripe_payment_intent_id == "pi_123456789"
        assert payment.status == PaymentStatus.REQUIRES_PAYMENT_METHOD
        mock_customer_repository.get.assert_called_once_with(customer_id)
        mock_stripe_service.create_payment_intent.assert_called_once_with(
            amount=1000,
            currency="usd",
            customer_id="cus_123456789",
            payment_method_id=None,
            metadata={}
        )

        # Step 2: Confirm payment intent
        # Mock payment retrieval
        mock_payment_repository.get.return_value = payment
        
        # Mock stripe payment intent confirmation
        mock_confirmed_intent = {
            "id": "pi_123456789",
            "status": "requires_capture"
        }
        stripe.PaymentIntent.confirm.return_value = mock_confirmed_intent
        
        # Mock updated payment
        confirmed_payment = Payment(
            id=payment_id,
            customer_id=customer_id,
            stripe_payment_intent_id="pi_123456789",
            amount=10.0,
            currency="usd",
            status=PaymentStatus.REQUIRES_CAPTURE,
            stripe_payment_method_id="pm_123456789"
        )
        mock_payment_repository.update.return_value = confirmed_payment
        
        # Confirm payment
        with patch('stripe.PaymentIntent.confirm', return_value=mock_confirmed_intent):
            updated_payment = await payment_service.confirm_payment_intent(
                payment_id=payment_id,
                payment_method_id="pm_123456789"
            )
        
        # Assert confirmation
        assert updated_payment.status == PaymentStatus.REQUIRES_CAPTURE
        assert updated_payment.stripe_payment_method_id == "pm_123456789"
        mock_payment_repository.get.assert_called_once_with(payment_id)
        
        # Step 3: Capture payment intent
        # Mock capture
        mock_captured_intent = {
            "id": "pi_123456789",
            "status": "succeeded"
        }
        
        # Mock updated payment
        captured_payment = Payment(
            id=payment_id,
            customer_id=customer_id,
            stripe_payment_intent_id="pi_123456789",
            amount=10.0,
            currency="usd",
            status=PaymentStatus.SUCCEEDED,
            stripe_payment_method_id="pm_123456789"
        )
        mock_payment_repository.update.return_value = captured_payment
        
        # Reset mock for get
        mock_payment_repository.get.reset_mock()
        mock_payment_repository.get.return_value = confirmed_payment
        
        # Reset mock for update
        mock_payment_repository.update.reset_mock()
        mock_payment_repository.update.return_value = captured_payment
        
        # Capture payment
        mock_stripe_service.capture_payment_intent.return_value = mock_captured_intent
        final_payment = await payment_service.capture_payment_intent(
            payment_id=payment_id
        )
        
        # Assert capture
        assert final_payment.status == PaymentStatus.SUCCEEDED
        mock_payment_repository.get.assert_called_once_with(payment_id)
        mock_stripe_service.capture_payment_intent.assert_called_once_with(
            "pi_123456789",
            amount_to_capture=None
        )
        mock_payment_repository.update.assert_called_once_with(
            payment_id,
            status=mock_captured_intent["status"]
        )

    @pytest.mark.asyncio
    async def test_payment_intent_cancelation(
        self, payment_service, mock_payment_repository, mock_stripe_service
    ):
        """Test canceling a payment intent"""
        # Setup mocks
        payment_id = 1
        payment = Payment(
            id=payment_id,
            customer_id=1,
            stripe_payment_intent_id="pi_123456789",
            amount=10.0,
            currency="usd",
            status=PaymentStatus.REQUIRES_PAYMENT_METHOD
        )
        mock_payment_repository.get.return_value = payment
        
        # Mock stripe cancelation
        mock_canceled_intent = {
            "id": "pi_123456789",
            "status": "canceled"
        }
        mock_stripe_service.cancel_payment_intent.return_value = mock_canceled_intent
        
        # Mock updated payment
        canceled_payment = Payment(
            id=payment_id,
            customer_id=1,
            stripe_payment_intent_id="pi_123456789",
            amount=10.0,
            currency="usd",
            status=PaymentStatus.CANCELED
        )
        mock_payment_repository.update.return_value = canceled_payment
        
        # Cancel payment
        result = await payment_service.cancel_payment_intent(payment_id)
        
        # Assert
        assert result.status == PaymentStatus.CANCELED
        mock_payment_repository.get.assert_called_once_with(payment_id)
        mock_stripe_service.cancel_payment_intent.assert_called_once_with("pi_123456789")
        mock_payment_repository.update.assert_called_once_with(
            payment_id,
            status=PaymentStatus.CANCELED
        )

    @pytest.mark.asyncio
    async def test_payment_webhook_handling(
        self, payment_service, mock_payment_repository, mock_stripe_service
    ):
        """Test handling payment webhooks"""
        # Setup mocks
        stripe_payment_intent_id = "pi_123456789"
        
        # 1. First sync when payment doesn't exist in our system
        mock_payment_repository.get_by_stripe_id.return_value = None
        
        # Mock customer retrieval
        customer = Customer(
            id=1,
            organization_id=1,
            stripe_customer_id="cus_123456789",
            tier=CustomerTier.STANDARD
        )
        mock_payment_service = MagicMock(spec=StripeService)
        payment_intent = {
            "id": stripe_payment_intent_id,
            "amount": 1000,
            "currency": "usd",
            "customer": "cus_123456789",
            "status": "succeeded",
            "payment_method": "pm_123456789",
            "payment_method_types": ["card"],
            "metadata": {}
        }
        mock_stripe_service.get_payment_intent.return_value = payment_intent
        mock_payment_service.customer_repository.get_by_stripe_id.return_value = customer
        
        # Mock created payment
        created_payment = Payment(
            id=1,
            customer_id=1,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=10.0,
            currency="usd",
            status=PaymentStatus.SUCCEEDED,
            stripe_payment_method_id="pm_123456789",
            payment_method=PaymentMethod.CARD
        )
        mock_payment_repository.create.return_value = created_payment
        
        # Call the webhook handler
        result = await payment_service.handle_payment_succeeded(stripe_payment_intent_id)
        
        # Assert that sync was attempted but no status update was needed 
        # since the payment was already in succeeded state
        assert result is True
        mock_payment_repository.get_by_stripe_id.assert_called_once_with(stripe_payment_intent_id)
        mock_stripe_service.get_payment_intent.assert_called_once_with(stripe_payment_intent_id)