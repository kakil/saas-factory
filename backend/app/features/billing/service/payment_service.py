import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.features.billing.models.payment import Payment, PaymentStatus, PaymentMethod
from app.features.billing.repository.payment_repository import PaymentRepository
from app.features.billing.repository.customer_repository import CustomerRepository
from app.features.billing.service.stripe_service import StripeService

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for managing payments
    Handles payment processing and status tracking
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        stripe_service: StripeService,
        payment_repository: PaymentRepository,
        customer_repository: CustomerRepository
    ):
        self.db = db
        self.stripe_service = stripe_service
        self.payment_repository = payment_repository
        self.customer_repository = customer_repository
    
    async def create_payment_intent(
        self,
        customer_id: int,
        amount: int,  # Amount in cents
        currency: str = "usd",
        payment_method_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        Create a payment intent for a customer
        
        Args:
            customer_id: Customer ID
            amount: Payment amount in cents
            currency: Currency code (default: 'usd')
            payment_method_id: Payment method to use (optional)
            description: Payment description (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Created payment object
            
        Raises:
            ValueError: If customer doesn't exist
        """
        # Get customer
        customer = await self.customer_repository.get(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Create payment intent in Stripe
        try:
            payment_intent = self.stripe_service.create_payment_intent(
                amount=amount,
                currency=currency,
                customer_id=customer.stripe_customer_id,
                payment_method_id=payment_method_id,
                metadata=metadata or {}
            )
            
            # Create local payment record
            payment = Payment(
                customer_id=customer_id,
                stripe_payment_intent_id=payment_intent["id"],
                stripe_payment_method_id=payment_method_id or payment_intent.get("payment_method"),
                amount=amount / 100.0,  # Convert from cents to dollars
                currency=currency,
                status=payment_intent["status"],
                payment_method=PaymentMethod.CARD,  # Default to card, will be updated later if needed
                description=description,
                metadata=metadata or {}
            )
            
            return await self.payment_repository.create(payment)
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe payment intent: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def confirm_payment_intent(
        self,
        payment_id: int,
        payment_method_id: Optional[str] = None
    ) -> Payment:
        """
        Confirm a payment intent
        
        Args:
            payment_id: Payment ID
            payment_method_id: Payment method to use (optional)
            
        Returns:
            Updated payment object
            
        Raises:
            ValueError: If payment doesn't exist or is in wrong state
        """
        # Get payment
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Ensure payment is in right state
        if payment.status != PaymentStatus.REQUIRES_CONFIRMATION and payment.status != PaymentStatus.REQUIRES_PAYMENT_METHOD:
            raise ValueError(f"Payment is not in confirmable state: {payment.status}")
        
        # Confirm in Stripe
        try:
            payment_intent = stripe.PaymentIntent.confirm(
                payment.stripe_payment_intent_id,
                payment_method=payment_method_id or payment.stripe_payment_method_id,
            )
            
            # Update local record
            update_data = {
                "status": payment_intent["status"],
            }
            
            if payment_method_id:
                update_data["stripe_payment_method_id"] = payment_method_id
            
            payment = await self.payment_repository.update(payment_id, **update_data)
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to confirm Stripe payment intent: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def capture_payment_intent(
        self,
        payment_id: int,
        amount_to_capture: Optional[int] = None
    ) -> Payment:
        """
        Capture an authorized payment intent
        
        Args:
            payment_id: Payment ID
            amount_to_capture: Amount to capture in cents (optional)
            
        Returns:
            Updated payment object
            
        Raises:
            ValueError: If payment doesn't exist or is in wrong state
        """
        # Get payment
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Ensure payment is authorized
        if payment.status != PaymentStatus.REQUIRES_CAPTURE:
            raise ValueError(f"Payment is not in capturable state: {payment.status}")
        
        # Capture in Stripe
        try:
            capture_args = {}
            if amount_to_capture:
                capture_args["amount_to_capture"] = amount_to_capture
                
            payment_intent = self.stripe_service.capture_payment_intent(
                payment.stripe_payment_intent_id,
                amount_to_capture=amount_to_capture
            )
            
            # Update local record
            payment = await self.payment_repository.update(
                payment_id,
                status=payment_intent["status"]
            )
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to capture Stripe payment intent: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def cancel_payment_intent(self, payment_id: int) -> Payment:
        """
        Cancel a payment intent
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Updated payment object
            
        Raises:
            ValueError: If payment doesn't exist or can't be canceled
        """
        # Get payment
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        # Ensure payment can be canceled
        if payment.status in [PaymentStatus.SUCCEEDED, PaymentStatus.CANCELED]:
            raise ValueError(f"Payment cannot be canceled: {payment.status}")
        
        # Cancel in Stripe
        try:
            payment_intent = self.stripe_service.cancel_payment_intent(payment.stripe_payment_intent_id)
            
            # Update local record
            payment = await self.payment_repository.update(
                payment_id,
                status=PaymentStatus.CANCELED
            )
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe payment intent: {str(e)}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def get_payment_by_stripe_id(self, stripe_payment_intent_id: str) -> Optional[Payment]:
        """
        Get a payment by Stripe payment intent ID
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment object or None if not found
        """
        stmt = select(Payment).where(Payment.stripe_payment_intent_id == stripe_payment_intent_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def sync_payment(self, stripe_payment_intent_id: str) -> Optional[Payment]:
        """
        Sync payment data from Stripe
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Updated payment object or None if not found
        """
        # Get payment by Stripe ID
        payment = await self.get_payment_by_stripe_id(stripe_payment_intent_id)
        
        # If not found, check if this is a new payment
        if not payment:
            # Try to create it if we have the customer
            try:
                # Get payment intent from Stripe
                payment_intent = self.stripe_service.get_payment_intent(stripe_payment_intent_id)
                
                # Get customer by Stripe ID
                stripe_customer_id = payment_intent.get("customer")
                if not stripe_customer_id:
                    logger.error(f"Payment {stripe_payment_intent_id} has no customer ID")
                    return None
                
                # Find customer
                customer = await self.customer_repository.get_by_stripe_id(stripe_customer_id)
                if not customer:
                    logger.error(f"Customer with Stripe ID {stripe_customer_id} not found")
                    return None
                
                # Create payment record
                payment = Payment(
                    customer_id=customer.id,
                    stripe_payment_intent_id=stripe_payment_intent_id,
                    stripe_payment_method_id=payment_intent.get("payment_method"),
                    amount=payment_intent["amount"] / 100.0,
                    currency=payment_intent["currency"],
                    status=payment_intent["status"],
                    payment_method=self._determine_payment_method(payment_intent),
                    description=payment_intent.get("description"),
                    metadata=payment_intent.get("metadata", {}),
                )
                
                if payment_intent.get("invoice"):
                    # Find invoice by Stripe ID
                    stmt = select(Invoice).where(Invoice.stripe_invoice_id == payment_intent["invoice"])
                    result = await self.db.execute(stmt)
                    invoice = result.scalars().first()
                    
                    if invoice:
                        payment.invoice_id = invoice.id
                
                # Save payment
                created_payment = await self.payment_repository.create(payment)
                return created_payment
                
            except Exception as e:
                logger.error(f"Failed to create payment from webhook: {str(e)}")
                return None
        
        # Update existing payment
        try:
            # Get data from Stripe
            payment_intent = self.stripe_service.get_payment_intent(stripe_payment_intent_id)
            
            # Extract data
            update_data = {
                "status": payment_intent["status"],
                "metadata": payment_intent.get("metadata", {}),
            }
            
            # Update payment method if available
            if payment_intent.get("payment_method"):
                update_data["stripe_payment_method_id"] = payment_intent["payment_method"]
                update_data["payment_method"] = self._determine_payment_method(payment_intent)
            
            # Update invoice if available
            if payment_intent.get("invoice") and not payment.invoice_id:
                # Find invoice by Stripe ID
                stmt = select(Invoice).where(Invoice.stripe_invoice_id == payment_intent["invoice"])
                result = await self.db.execute(stmt)
                invoice = result.scalars().first()
                
                if invoice:
                    update_data["invoice_id"] = invoice.id
            
            # Update payment
            payment = await self.payment_repository.update(payment.id, **update_data)
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync payment from Stripe: {str(e)}")
            return payment
    
    async def handle_payment_succeeded(self, stripe_payment_intent_id: str) -> bool:
        """
        Handle payment succeeded event
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Success flag
        """
        # Find or sync payment
        payment = await self.get_payment_by_stripe_id(stripe_payment_intent_id)
        if not payment:
            payment = await self.sync_payment(stripe_payment_intent_id)
            if not payment:
                logger.error(f"Failed to sync payment {stripe_payment_intent_id}")
                return False
        
        # Update status
        try:
            await self.payment_repository.update(
                payment.id,
                status=PaymentStatus.SUCCEEDED
            )
            
            # TODO: Send payment succeeded notification
            
            return True
        except Exception as e:
            logger.error(f"Failed to update payment status: {str(e)}")
            return False
    
    async def handle_payment_failed(self, stripe_payment_intent_id: str) -> bool:
        """
        Handle payment failed event
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Success flag
        """
        # Find or sync payment
        payment = await self.get_payment_by_stripe_id(stripe_payment_intent_id)
        if not payment:
            payment = await self.sync_payment(stripe_payment_intent_id)
            if not payment:
                logger.error(f"Failed to sync payment {stripe_payment_intent_id}")
                return False
        
        # Update status
        try:
            # Get failure message from Stripe
            payment_intent = self.stripe_service.get_payment_intent(stripe_payment_intent_id)
            last_error = payment_intent.get("last_payment_error", {})
            failure_message = last_error.get("message", "Payment failed")
            
            await self.payment_repository.update(
                payment.id,
                status=PaymentStatus.FAILED,
                failure_message=failure_message
            )
            
            # TODO: Send payment failed notification
            
            return True
        except Exception as e:
            logger.error(f"Failed to update payment status: {str(e)}")
            return False
    
    async def handle_payment_canceled(self, stripe_payment_intent_id: str) -> bool:
        """
        Handle payment canceled event
        
        Args:
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Success flag
        """
        # Find or sync payment
        payment = await self.get_payment_by_stripe_id(stripe_payment_intent_id)
        if not payment:
            payment = await self.sync_payment(stripe_payment_intent_id)
            if not payment:
                logger.error(f"Failed to sync payment {stripe_payment_intent_id}")
                return False
        
        # Update status
        try:
            await self.payment_repository.update(
                payment.id,
                status=PaymentStatus.CANCELED
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update payment status: {str(e)}")
            return False
    
    def _determine_payment_method(self, payment_intent: Dict[str, Any]) -> str:
        """
        Determine payment method type from Stripe payment intent
        
        Args:
            payment_intent: Stripe payment intent object
            
        Returns:
            Payment method type
        """
        if not payment_intent.get("payment_method_types"):
            return PaymentMethod.CARD  # Default to card
        
        # Get first payment method type
        payment_method_type = payment_intent["payment_method_types"][0]
        
        # Map to our enum if possible
        return getattr(PaymentMethod, payment_method_type.upper(), PaymentMethod.OTHER)