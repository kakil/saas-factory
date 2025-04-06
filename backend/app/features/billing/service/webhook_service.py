import json
import logging
from typing import Any, Dict, Optional

import stripe
from fastapi import Request, HTTPException, BackgroundTasks

from app.core.config.settings import settings
from app.features.billing.service.stripe_service import StripeService
from app.features.billing.service.subscription_service import SubscriptionService
from app.features.billing.service.invoice_service import InvoiceService
from app.features.billing.service.payment_service import PaymentService
from app.features.billing.service.customer_service import CustomerService

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for handling Stripe webhooks
    Processes webhook events and updates local database
    """
    
    def __init__(
        self,
        stripe_service: StripeService,
        subscription_service: SubscriptionService,
        invoice_service: InvoiceService,
        payment_service: PaymentService,
        customer_service: CustomerService,
    ):
        self.stripe_service = stripe_service
        self.subscription_service = subscription_service
        self.invoice_service = invoice_service
        self.payment_service = payment_service
        self.customer_service = customer_service
    
    async def process_webhook(self, request: Request, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """
        Process a Stripe webhook event
        
        Args:
            request: FastAPI request object
            background_tasks: FastAPI background tasks object
            
        Returns:
            Response indicating successful processing
            
        Raises:
            HTTPException: If webhook validation fails
        """
        # Get signature from headers
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Get request body
        payload = await request.body()
        
        try:
            # Verify and parse the event
            event = self.stripe_service.construct_event(payload, sig_header)
            logger.info(f"Received webhook event: {event.type}")
            
            # Process the event
            event_data = event.data.object
            
            # Handle events in background tasks to respond quickly to Stripe
            background_tasks.add_task(self._process_event, event.type, event_data)
            
            return {"status": "success", "message": f"Webhook received: {event.type}"}
            
        except ValueError as e:
            # Invalid payload or signature
            logger.error(f"Webhook validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # General error
            logger.error(f"Webhook processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Process a webhook event based on its type
        
        Args:
            event_type: Type of Stripe event
            event_data: Event data from Stripe
        """
        logger.debug(f"Processing event: {event_type} with data: {json.dumps(event_data)}")
        
        # Customer events
        if event_type.startswith("customer"):
            if event_type == "customer.created":
                await self.customer_service.sync_customer(event_data.id)
            elif event_type == "customer.updated":
                await self.customer_service.sync_customer(event_data.id)
            elif event_type == "customer.deleted":
                await self.customer_service.mark_customer_deleted(event_data.id)
        
        # Subscription events
        elif event_type.startswith("customer.subscription"):
            if event_type == "customer.subscription.created":
                await self.subscription_service.sync_subscription(event_data.id)
            elif event_type == "customer.subscription.updated":
                await self.subscription_service.sync_subscription(event_data.id)
            elif event_type == "customer.subscription.deleted":
                await self.subscription_service.mark_subscription_deleted(event_data.id)
            elif event_type == "customer.subscription.trial_will_end":
                # Handle trial ending soon (3 days before)
                await self.subscription_service.handle_trial_ending(event_data.id)
            elif event_type == "customer.subscription.pending_update_applied":
                # Handle when a scheduled subscription update is applied
                await self.subscription_service.sync_subscription(event_data.id)
            elif event_type == "customer.subscription.pending_update_expired":
                # Handle when a scheduled subscription update expires
                await self.subscription_service.sync_subscription(event_data.id)
            elif event_type == "customer.subscription.payment_failed":
                # Handle when a subscription payment fails
                await self.subscription_service.handle_payment_failed(event_data.id)
            elif event_type == "invoice.upcoming":
                # Handle upcoming invoice - this can be used for renewal notifications
                if event_data.get('subscription'):
                    await self.subscription_service.handle_subscription_renewing(event_data.subscription)
        
        # Invoice events
        elif event_type.startswith("invoice"):
            if event_type == "invoice.created":
                await self.invoice_service.sync_invoice(event_data.id)
            elif event_type == "invoice.updated":
                await self.invoice_service.sync_invoice(event_data.id)
            elif event_type == "invoice.deleted":
                await self.invoice_service.mark_invoice_deleted(event_data.id)
            elif event_type == "invoice.payment_succeeded":
                await self.invoice_service.handle_payment_succeeded(event_data.id)
            elif event_type == "invoice.payment_failed":
                await self.invoice_service.handle_payment_failed(event_data.id)
            elif event_type == "invoice.finalized":
                await self.invoice_service.handle_invoice_finalized(event_data.id)
        
        # Payment Intent events
        elif event_type.startswith("payment_intent"):
            if event_type == "payment_intent.succeeded":
                await self.payment_service.handle_payment_succeeded(event_data.id)
            elif event_type == "payment_intent.payment_failed":
                await self.payment_service.handle_payment_failed(event_data.id)
            elif event_type == "payment_intent.canceled":
                await self.payment_service.handle_payment_canceled(event_data.id)
        
        # Payment Method events
        elif event_type.startswith("payment_method"):
            if event_type == "payment_method.attached":
                await self.customer_service.handle_payment_method_attached(
                    event_data.customer, event_data.id
                )
            elif event_type == "payment_method.detached":
                await self.customer_service.handle_payment_method_detached(event_data.id)
        
        # Log unhandled events
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            
        logger.debug(f"Finished processing event: {event_type}")