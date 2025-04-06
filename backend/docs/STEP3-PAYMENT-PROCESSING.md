# SaaS Factory - Payment Processing Framework

This document provides an overview of the payment processing framework implemented in Step 3 of the SaaS Factory Blueprint application.

## Overview

The payment processing framework integrates with Stripe to provide robust billing capabilities for your SaaS application. It includes three main components:

1. **Stripe Integration** - Direct API integration with Stripe's payment platform
2. **Subscription Management** - Comprehensive subscription lifecycle management
3. **Invoice Handling** - Automated invoice generation and management

## Architecture

The billing system follows a layered architecture:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    API      │ --> │   Services  │ --> │ Repositories│ --> │   Models    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                                       │
       │                   │                                       │
       │                   ▼                                       │
       │            ┌─────────────┐                               │
       └───────────┤  Schemas     │◄──────────────────────────────┘
                    └─────────────┘
```

- **Models**: Database entities mapping to Stripe resources
- **Repositories**: Data access layer for CRUD operations
- **Services**: Business logic and Stripe API interactions
- **API Endpoints**: REST endpoints for frontend interaction
- **Schemas**: Data validation and transformation

## Key Components

### 1. Stripe Integration

The core Stripe integration is handled by the `StripeService` which provides methods for:

- Customer management
- Payment method handling
- Product and price management
- Subscription operations
- Invoice operations
- Payment processing
- Webhook handling

#### Usage Example:

```python
# Create a customer in Stripe
customer_data = await stripe_service.create_customer(
    email="customer@example.com",
    name="Example Customer",
    metadata={"organization_id": "123"}
)

# Retrieve customer data
customer = await stripe_service.get_customer(customer_id)
```

### 2. Subscription Management

The `SubscriptionService` handles subscription lifecycle events:

- Creating subscriptions
- Upgrading/downgrading plans
- Scheduling future changes
- Handling trial periods
- Processing renewals and cancellations

#### Subscription States:

- `ACTIVE` - Current and valid subscription
- `PAST_DUE` - Payment failed but still active
- `UNPAID` - Payment failed and subscription inactive
- `CANCELED` - Subscription canceled
- `TRIALING` - In trial period
- `INCOMPLETE` - Setup incomplete
- `INCOMPLETE_EXPIRED` - Setup failed

#### Usage Example:

```python
# Create a new subscription
subscription = await subscription_service.create_subscription(
    customer_id=1,
    plan_id=2,
    trial_days=14
)

# Upgrade a subscription
updated_subscription = await subscription_service.upgrade_subscription(
    subscription_id=1,
    plan_id=3,
    effective_date=datetime.now() + timedelta(days=30),
    prorate=True
)
```

### 3. Invoice Handling

The `InvoiceService` manages all aspects of invoicing:

- Invoice generation
- Payment collection
- Status tracking
- Retrieving invoice history

#### Invoice States:

- `DRAFT` - Not finalized
- `OPEN` - Finalized but unpaid
- `PAID` - Fully paid
- `UNCOLLECTIBLE` - Failed payment
- `VOID` - Voided invoice

#### Usage Example:

```python
# Get invoice details
invoice = await invoice_service.get_invoice(invoice_id=123)

# Get customer's recent invoices
invoices = await invoice_service.get_customer_invoices(
    customer_id=1,
    limit=10
)
```

## Webhook Processing

The system processes Stripe webhooks to synchronize events:

1. Webhooks arrive at the `/billing/webhooks` endpoint
2. `WebhookService` validates the event signature
3. Event is processed based on type (customer, subscription, invoice, payment)
4. Database is updated to reflect Stripe state
5. Additional business logic executed as needed

### Supported Webhook Events:

- `customer.created`, `customer.updated`
- `customer.subscription.created`, `customer.subscription.updated`
- `invoice.created`, `invoice.payment_succeeded`
- `payment_intent.succeeded`, `payment_intent.failed`

## Organization/User Integration

Billing connects to the application's user/organization system:

- Each organization has one Customer record
- Subscriptions tie to organization tiers
- Invoices and payments link to the organization
- Billing status affects feature availability

## API Endpoints

The billing system exposes these REST endpoints:

- `/plans` - Available subscription plans
- `/customers` - Customer management
- `/subscriptions` - Subscription operations
- `/invoices` - Invoice retrieval and management
- `/payments` - Payment method management
- `/organizations/{id}/billing` - Organization billing info
- `/webhooks` - Stripe webhook receiver

## Data Models

### Customer

Maps to Stripe Customer object and links to an Organization:

```python
class Customer(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    stripe_customer_id: Mapped[Optional[str]]
    tier: Mapped[CustomerTier] = mapped_column(default=CustomerTier.FREE)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    email: Mapped[str]
    name: Mapped[Optional[str]]
    # Additional fields...
```

### Plan

Represents a product offering with pricing tiers:

```python
class Plan(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    stripe_product_id: Mapped[Optional[str]]
    name: Mapped[str]
    description: Mapped[Optional[str]]
    interval: Mapped[Optional[BillingInterval]]
    is_active: Mapped[bool] = mapped_column(default=True)
    # Additional fields...
```

### Subscription

Tracks a customer's subscription to a plan:

```python
class Subscription(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    stripe_subscription_id: Mapped[Optional[str]]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan.id"))
    status: Mapped[SubscriptionStatus]
    current_period_start: Mapped[Optional[datetime]]
    current_period_end: Mapped[Optional[datetime]]
    # Additional fields...
```

## Setup and Configuration

To use the billing system, ensure these environment variables are set:

```
STRIPE_API_KEY=sk_test_your_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PUBLIC_KEY=pk_test_your_public_key
```

## Testing

The billing system includes comprehensive tests:

1. Unit tests for service methods
2. Integration tests with Stripe API
3. Mock webhook event processing tests

Run billing tests with:

```bash
pytest tests/features/billing/
```

## Extending the Framework

To add a new billing feature:

1. Update the relevant model(s)
2. Create or update repository methods
3. Add service methods with business logic
4. Create API endpoints if needed
5. Add any required webhook handling

## Common Operations

### Creating a New Plan

```python
# In the database
new_plan = Plan(
    name="Premium",
    description="Premium tier with advanced features",
    interval=BillingInterval.MONTHLY,
    is_active=True
)
db.add(new_plan)
await db.commit()

# In Stripe
stripe_product = await stripe_service.create_product(
    name="Premium",
    description="Premium tier with advanced features"
)

stripe_price = await stripe_service.create_price(
    product_id=stripe_product["id"],
    unit_amount=2999,  # $29.99
    currency="usd",
    interval="month"
)

# Update the database plan with Stripe IDs
new_plan.stripe_product_id = stripe_product["id"]
await db.commit()
```

### Subscribing a Customer to a Plan

```python
# Create customer if needed
customer = await customer_service.get_or_create_customer(
    organization_id=org.id,
    email=org.owner_email,
    name=org.name
)

# Create subscription
subscription = await subscription_service.create_subscription(
    customer_id=customer.id,
    plan_id=plan.id,
    trial_days=14
)

# Update organization tier based on plan
await customer_service.update_organization_billing_tier(
    organization_id=org.id,
    tier=CustomerTier.PREMIUM
)
```

## Troubleshooting

### Common Issues

1. **Webhook Signature Verification Failed**
   - Check STRIPE_WEBHOOK_SECRET environment variable
   - Ensure webhook URL is correctly configured in Stripe dashboard

2. **Subscription Status Mismatch**
   - Check webhook processing for missed events
   - Manually sync with `subscription_service.sync_subscription()`

3. **Payment Failures**
   - Verify payment method status
   - Check webhook processing for payment_intent.failed events

### Useful Commands

Sync a specific subscription with Stripe:
```python
await subscription_service.sync_subscription(stripe_subscription_id="sub_123")
```

Manually trigger an invoice payment:
```python
await invoice_service.pay_invoice(invoice_id=123)
```

## Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Webhook Events](https://stripe.com/docs/api/events/types)
- [Stripe Testing](https://stripe.com/docs/testing)