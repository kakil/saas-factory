import pytest
from unittest.mock import patch, MagicMock
import stripe

from app.features.billing.service.stripe_service import StripeService


@pytest.fixture
def stripe_service():
    with patch('stripe.api_key'):
        yield StripeService()


class TestStripeService:
    """Tests for the StripeService class"""

    @patch('stripe.Customer.create')
    def test_create_customer(self, mock_create, stripe_service):
        # Setup mock
        mock_customer = {
            "id": "cus_123456789",
            "email": "test@example.com",
            "name": "Test Customer",
            "metadata": {"organization_id": "123"}
        }
        mock_create.return_value = mock_customer

        # Call the function
        result = stripe_service.create_customer(
            email="test@example.com",
            name="Test Customer",
            metadata={"organization_id": "123"}
        )

        # Assert
        mock_create.assert_called_once_with(
            email="test@example.com",
            name="Test Customer",
            metadata={"organization_id": "123"}
        )
        assert result == mock_customer

    @patch('stripe.Product.create')
    def test_create_product(self, mock_create, stripe_service):
        # Setup mock
        mock_product = {
            "id": "prod_123456789",
            "name": "Test Plan",
            "description": "Test Description",
            "metadata": {"feature": "all"}
        }
        mock_create.return_value = mock_product

        # Call the function
        result = stripe_service.create_product(
            name="Test Plan",
            description="Test Description",
            metadata={"feature": "all"}
        )

        # Assert
        mock_create.assert_called_once_with(
            name="Test Plan",
            description="Test Description",
            metadata={"feature": "all"}
        )
        assert result == mock_product

    @patch('stripe.Price.create')
    def test_create_price(self, mock_create, stripe_service):
        # Setup mock
        mock_price = {
            "id": "price_123456789",
            "product": "prod_123456789",
            "unit_amount": 1000,
            "currency": "usd",
            "recurring": {"interval": "month"}
        }
        mock_create.return_value = mock_price

        # Call the function
        result = stripe_service.create_price(
            product_id="prod_123456789",
            amount=1000,
            currency="usd",
            interval="month"
        )

        # Assert
        mock_create.assert_called_once_with(
            product="prod_123456789",
            unit_amount=1000,
            currency="usd",
            recurring={"interval": "month", "interval_count": 1},
            metadata={}
        )
        assert result == mock_price

    @patch('stripe.Subscription.create')
    def test_create_subscription(self, mock_create, stripe_service):
        # Setup mock
        mock_subscription = {
            "id": "sub_123456789",
            "customer": "cus_123456789",
            "status": "active",
            "current_period_start": 1609459200,
            "current_period_end": 1612137600,
            "items": {
                "data": [
                    {
                        "id": "si_123456789",
                        "price": "price_123456789",
                        "quantity": 1
                    }
                ]
            }
        }
        mock_create.return_value = mock_subscription

        # Call the function
        result = stripe_service.create_subscription(
            customer_id="cus_123456789",
            price_id="price_123456789"
        )

        # Assert
        mock_create.assert_called_once_with(
            customer="cus_123456789",
            items=[
                {
                    "price": "price_123456789",
                    "quantity": 1,
                },
            ],
            metadata={}
        )
        assert result == mock_subscription

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent(self, mock_create, stripe_service):
        # Setup mock
        mock_payment_intent = {
            "id": "pi_123456789",
            "amount": 1000,
            "currency": "usd",
            "customer": "cus_123456789",
            "status": "requires_payment_method"
        }
        mock_create.return_value = mock_payment_intent

        # Call the function
        result = stripe_service.create_payment_intent(
            amount=1000,
            currency="usd",
            customer_id="cus_123456789"
        )

        # Assert
        mock_create.assert_called_once_with(
            amount=1000,
            currency="usd",
            customer="cus_123456789",
            metadata={}
        )
        assert result == mock_payment_intent

    @patch('stripe.Webhook.construct_event')
    def test_construct_event(self, mock_construct, stripe_service):
        # Setup mock
        payload = b'{"id": "evt_123456789"}'
        sig_header = "signature"
        mock_event = stripe.Event.construct_from(
            {"id": "evt_123456789", "type": "payment_intent.succeeded"},
            "secret"
        )
        mock_construct.return_value = mock_event

        # Call the function
        result = stripe_service.construct_event(payload, sig_header)

        # Assert
        mock_construct.assert_called_once_with(
            payload=payload,
            sig_header=sig_header,
            secret=stripe_service.webhook_secret
        )
        assert result == mock_event

    @patch('stripe.Webhook.construct_event')
    def test_construct_event_invalid_signature(self, mock_construct, stripe_service):
        # Setup mock
        payload = b'{"id": "evt_123456789"}'
        sig_header = "invalid_signature"
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", sig_header)

        # Call the function and assert exception
        with pytest.raises(ValueError) as exc_info:
            stripe_service.construct_event(payload, sig_header)

        assert "Invalid signature" in str(exc_info.value)