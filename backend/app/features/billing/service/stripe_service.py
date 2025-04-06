import logging
import stripe
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class StripeService:
    """
    Base service for Stripe integrations
    Provides common functionality for interacting with the Stripe API
    """
    
    def __init__(self):
        """Initialize the Stripe service with API key from settings"""
        self.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        stripe.api_key = self.api_key
    
    # Customers
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new customer in Stripe
        
        Args:
            email: Customer email address
            name: Customer name (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Stripe customer object
        """
        customer_data = {
            "email": email,
            "metadata": metadata or {},
        }
        
        if name:
            customer_data["name"] = name
            
        return stripe.Customer.create(**customer_data)
    
    def update_customer(self, customer_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing customer in Stripe
        
        Args:
            customer_id: Stripe customer ID
            **kwargs: Fields to update
            
        Returns:
            Updated Stripe customer object
        """
        return stripe.Customer.modify(customer_id, **kwargs)
    
    def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Delete a customer from Stripe
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Deleted customer object
        """
        return stripe.Customer.delete(customer_id)
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve a customer from Stripe
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Stripe customer object
        """
        return stripe.Customer.retrieve(customer_id)
    
    # Payment Methods
    def add_payment_method(self, customer_id: str, payment_method_id: str, set_as_default: bool = True) -> Dict[str, Any]:
        """
        Add a payment method to a customer
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            set_as_default: Whether to set as default payment method
            
        Returns:
            Payment method object
        """
        # Attach payment method to customer
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )
        
        # Set as default if requested
        if set_as_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )
            
        return payment_method
    
    def remove_payment_method(self, payment_method_id: str) -> Dict[str, Any]:
        """
        Remove a payment method
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            Detached payment method object
        """
        return stripe.PaymentMethod.detach(payment_method_id)
    
    def list_payment_methods(self, customer_id: str, type: str = "card") -> List[Dict[str, Any]]:
        """
        List payment methods for a customer
        
        Args:
            customer_id: Stripe customer ID
            type: Payment method type (default: 'card')
            
        Returns:
            List of payment methods
        """
        return stripe.PaymentMethod.list(
            customer=customer_id,
            type=type,
        )
    
    # Products and Prices
    def create_product(self, name: str, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new product in Stripe
        
        Args:
            name: Product name
            description: Product description (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Stripe product object
        """
        product_data = {
            "name": name,
            "metadata": metadata or {},
        }
        
        if description:
            product_data["description"] = description
            
        return stripe.Product.create(**product_data)
    
    def update_product(self, product_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a product in Stripe
        
        Args:
            product_id: Stripe product ID
            **kwargs: Fields to update
            
        Returns:
            Updated product object
        """
        return stripe.Product.modify(product_id, **kwargs)
    
    def archive_product(self, product_id: str) -> Dict[str, Any]:
        """
        Archive a product (set active=False)
        
        Args:
            product_id: Stripe product ID
            
        Returns:
            Updated product object
        """
        return stripe.Product.modify(product_id, active=False)
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieve a product from Stripe
        
        Args:
            product_id: Stripe product ID
            
        Returns:
            Product object
        """
        return stripe.Product.retrieve(product_id)
    
    def list_products(self, active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List products in Stripe
        
        Args:
            active: Filter by active status (optional)
            limit: Maximum number of products to return
            
        Returns:
            List of products
        """
        params = {"limit": limit}
        
        if active is not None:
            params["active"] = active
            
        return stripe.Product.list(**params)
    
    def create_price(self, product_id: str, amount: int, currency: str = "usd", interval: Optional[str] = None, 
                    interval_count: int = 1, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new price for a product
        
        Args:
            product_id: Stripe product ID
            amount: Price amount in smallest currency unit (cents for USD)
            currency: Currency code (default: 'usd')
            interval: Billing interval for recurring prices ('month', 'year', etc.) (optional)
            interval_count: Number of intervals between billings (default: 1)
            metadata: Additional metadata (optional)
            
        Returns:
            Stripe price object
        """
        price_data = {
            "product": product_id,
            "unit_amount": amount,
            "currency": currency,
            "metadata": metadata or {},
        }
        
        # One-time vs recurring price
        if interval:
            price_data["recurring"] = {
                "interval": interval,
                "interval_count": interval_count,
            }
            
        return stripe.Price.create(**price_data)
    
    def get_price(self, price_id: str) -> Dict[str, Any]:
        """
        Retrieve a price from Stripe
        
        Args:
            price_id: Stripe price ID
            
        Returns:
            Price object
        """
        return stripe.Price.retrieve(price_id)
    
    def list_prices(self, product_id: Optional[str] = None, active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List prices in Stripe
        
        Args:
            product_id: Filter by product ID (optional)
            active: Filter by active status (optional)
            limit: Maximum number of prices to return
            
        Returns:
            List of prices
        """
        params = {"limit": limit}
        
        if product_id:
            params["product"] = product_id
            
        if active is not None:
            params["active"] = active
            
        return stripe.Price.list(**params)
    
    # Subscriptions
    def create_subscription(self, customer_id: str, price_id: str, quantity: int = 1, 
                           trial_days: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new subscription for a customer
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            quantity: Number of units (default: 1)
            trial_days: Number of trial days (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Stripe subscription object
        """
        subscription_data = {
            "customer": customer_id,
            "items": [
                {
                    "price": price_id,
                    "quantity": quantity,
                },
            ],
            "metadata": metadata or {},
        }
        
        if trial_days:
            subscription_data["trial_period_days"] = trial_days
            
        return stripe.Subscription.create(**subscription_data)
    
    def update_subscription(self, subscription_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing subscription
        
        Args:
            subscription_id: Stripe subscription ID
            **kwargs: Fields to update
            
        Returns:
            Updated subscription object
        """
        return stripe.Subscription.modify(subscription_id, **kwargs)
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            Updated subscription object
        """
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=at_period_end,
        )
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve a subscription from Stripe
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription object
        """
        return stripe.Subscription.retrieve(subscription_id)
    
    def list_subscriptions(self, customer_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List subscriptions in Stripe
        
        Args:
            customer_id: Filter by customer ID (optional)
            status: Filter by status (optional)
            limit: Maximum number of subscriptions to return
            
        Returns:
            List of subscriptions
        """
        params = {"limit": limit}
        
        if customer_id:
            params["customer"] = customer_id
            
        if status:
            params["status"] = status
            
        return stripe.Subscription.list(**params)
    
    # Invoices
    def create_invoice(self, customer_id: str, auto_advance: bool = True, 
                      collection_method: str = "charge_automatically", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new invoice for a customer
        
        Args:
            customer_id: Stripe customer ID
            auto_advance: Whether to finalize the invoice automatically
            collection_method: Collection method ('charge_automatically' or 'send_invoice')
            metadata: Additional metadata (optional)
            
        Returns:
            Stripe invoice object
        """
        return stripe.Invoice.create(
            customer=customer_id,
            auto_advance=auto_advance,
            collection_method=collection_method,
            metadata=metadata or {},
        )
    
    def finalize_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Finalize a draft invoice
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Finalized invoice object
        """
        return stripe.Invoice.finalize_invoice(invoice_id)
    
    def pay_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Pay an invoice
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Paid invoice object
        """
        return stripe.Invoice.pay(invoice_id)
    
    def void_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Void an invoice
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Voided invoice object
        """
        return stripe.Invoice.void_invoice(invoice_id)
    
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Retrieve an invoice from Stripe
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Invoice object
        """
        return stripe.Invoice.retrieve(invoice_id)
    
    def list_invoices(self, customer_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List invoices in Stripe
        
        Args:
            customer_id: Filter by customer ID (optional)
            status: Filter by status (optional)
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoices
        """
        params = {"limit": limit}
        
        if customer_id:
            params["customer"] = customer_id
            
        if status:
            params["status"] = status
            
        return stripe.Invoice.list(**params)
    
    # Payments
    def create_payment_intent(self, amount: int, currency: str = "usd", customer_id: Optional[str] = None, 
                             payment_method_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a payment intent
        
        Args:
            amount: Payment amount in smallest currency unit
            currency: Currency code (default: 'usd')
            customer_id: Stripe customer ID (optional)
            payment_method_id: Payment method to use (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Payment intent object
        """
        intent_data = {
            "amount": amount,
            "currency": currency,
            "metadata": metadata or {},
        }
        
        if customer_id:
            intent_data["customer"] = customer_id
            
        if payment_method_id:
            intent_data["payment_method"] = payment_method_id
            intent_data["confirm"] = True
            
        return stripe.PaymentIntent.create(**intent_data)
    
    def capture_payment_intent(self, payment_intent_id: str, amount_to_capture: Optional[int] = None) -> Dict[str, Any]:
        """
        Capture an authorized payment intent
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount_to_capture: Amount to capture (optional, defaults to entire amount)
            
        Returns:
            Captured payment intent object
        """
        capture_params = {}
        
        if amount_to_capture:
            capture_params["amount_to_capture"] = amount_to_capture
            
        return stripe.PaymentIntent.capture(payment_intent_id, **capture_params)
    
    def cancel_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Cancel a payment intent
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Canceled payment intent object
        """
        return stripe.PaymentIntent.cancel(payment_intent_id)
    
    def get_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent from Stripe
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment intent object
        """
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    
    # Webhooks
    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Construct a Stripe event from webhook payload
        
        Args:
            payload: Request body as bytes
            sig_header: Stripe signature header
            
        Returns:
            Stripe event object
            
        Raises:
            ValueError: If webhook signature verification fails
        """
        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=self.webhook_secret,
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            raise ValueError(f"Invalid signature: {str(e)}")
    
    # Subscription Schedules
    def create_subscription_schedule(
        self, 
        stripe_subscription_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        start_date: Optional[int] = None,
        end_behavior: str = "release",
        phases: Optional[List[Dict[str, Any]]] = None,
        price_id: Optional[str] = None,
        quantity: int = 1,
        proration_behavior: str = "create_prorations",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription schedule for future plan changes
        
        Args:
            stripe_subscription_id: Existing subscription ID to schedule changes for (optional)
            customer_id: Stripe customer ID for new schedules (required if no subscription_id)
            start_date: When the schedule should start (timestamp)
            end_behavior: What to do when schedule ends ('release' or 'cancel')
            phases: Schedule phases configuration (optional)
            price_id: Price ID to use (if creating a simple schedule)
            quantity: Quantity for the price (default: 1)
            proration_behavior: How to handle prorations ('create_prorations' or 'none')
            metadata: Additional metadata (optional)
            
        Returns:
            Subscription schedule object
        """
        # If we're scheduling a change to an existing subscription
        if stripe_subscription_id:
            # Get current subscription details
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            customer_id = subscription["customer"]
            
            # If no start date provided, default to end of current period
            if not start_date:
                start_date = subscription["current_period_end"]
                
            # If no phases provided, build phases from current subscription
            if not phases:
                if not price_id:
                    raise ValueError("Either phases or price_id must be provided for subscription schedule")
                
                # Create a simple two-phase schedule
                current_items = [{
                    "price": item["price"]["id"],
                    "quantity": item["quantity"]
                } for item in subscription["items"]["data"]]
                
                # Current phase - from now until start_date
                current_phase = {
                    "items": current_items,
                    "start_date": "now",
                    "end_date": start_date,
                    "proration_behavior": "none"
                }
                
                # New phase - from start_date onward
                new_phase = {
                    "items": [{
                        "price": price_id,
                        "quantity": quantity
                    }],
                    "proration_behavior": proration_behavior
                }
                
                phases = [current_phase, new_phase]
        else:
            # For brand new scheduled subscriptions
            if not customer_id:
                raise ValueError("Customer ID is required for new subscription schedules")
                
            if not phases and not price_id:
                raise ValueError("Either phases or price_id must be provided for subscription schedule")
                
            # If no phases but price_id is provided, create a simple one-phase schedule
            if not phases:
                start_date = start_date or int(datetime.now().timestamp())
                
                phases = [{
                    "items": [{
                        "price": price_id,
                        "quantity": quantity
                    }],
                    "start_date": start_date,
                    "proration_behavior": proration_behavior
                }]
        
        # Create the schedule
        schedule_data = {
            "customer": customer_id,
            "start_date": phases[0]["start_date"],
            "end_behavior": end_behavior,
            "phases": phases,
            "metadata": metadata or {}
        }
        
        # If we're basing this on an existing subscription
        if stripe_subscription_id:
            schedule_data["from_subscription"] = stripe_subscription_id
            
        return stripe.SubscriptionSchedule.create(**schedule_data)
    
    def update_subscription_schedule(self, schedule_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing subscription schedule
        
        Args:
            schedule_id: Subscription schedule ID
            **kwargs: Fields to update
            
        Returns:
            Updated subscription schedule object
        """
        return stripe.SubscriptionSchedule.modify(schedule_id, **kwargs)
    
    def cancel_subscription_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription schedule
        
        Args:
            schedule_id: Subscription schedule ID
            
        Returns:
            Canceled subscription schedule object
        """
        return stripe.SubscriptionSchedule.release(schedule_id)
    
    def get_subscription_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Retrieve a subscription schedule from Stripe
        
        Args:
            schedule_id: Subscription schedule ID
            
        Returns:
            Subscription schedule object
        """
        return stripe.SubscriptionSchedule.retrieve(schedule_id)
    
    def list_subscription_schedules(self, customer_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List subscription schedules
        
        Args:
            customer_id: Filter by customer ID (optional)
            limit: Maximum number of schedules to return
            
        Returns:
            List of subscription schedules
        """
        params = {"limit": limit}
        
        if customer_id:
            params["customer"] = customer_id
            
        return stripe.SubscriptionSchedule.list(**params)
        
    # Usage Records for Usage-Based Billing
    def create_usage_record(self, subscription_item_id: str, quantity: int, timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a usage record for metered billing
        
        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity to report
            timestamp: When the usage occurred (optional)
            
        Returns:
            Usage record object
        """
        usage_data = {
            "quantity": quantity,
            "action": "increment"
        }
        
        if timestamp:
            usage_data["timestamp"] = timestamp
            
        return stripe.SubscriptionItem.create_usage_record(subscription_item_id, **usage_data)
    
    def list_usage_records(self, subscription_item_id: str) -> List[Dict[str, Any]]:
        """
        List usage records for a subscription item
        
        Args:
            subscription_item_id: Stripe subscription item ID
            
        Returns:
            List of usage records
        """
        return stripe.SubscriptionItem.list_usage_record_summaries(subscription_item_id)
    
    # Error handling
    def handle_stripe_error(self, error: stripe.error.StripeError) -> Dict[str, Any]:
        """
        Handle Stripe errors and return standardized response
        
        Args:
            error: Stripe error object
            
        Returns:
            Standardized error response
        """
        error_data = {
            "status": "error",
            "type": error.__class__.__name__,
            "code": error.code if hasattr(error, "code") else None,
            "param": error.param if hasattr(error, "param") else None,
            "message": str(error),
        }
        
        return error_data