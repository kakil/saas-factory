"""Add billing models

Revision ID: 5d6f8e29c7b8
Revises: 4c8d0a57d9b6
Create Date: 2025-04-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5d6f8e29c7b8'
down_revision: str = '4c8d0a57d9b6'  # This references the previous migration (notifications)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum types for billing models
    customer_tier = sa.Enum(
        'free', 'starter', 'pro', 'enterprise',
        name='customertier'
    )
    
    plan_interval = sa.Enum(
        'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'custom',
        name='planinterval'
    )
    
    price_type = sa.Enum(
        'one_time', 'recurring', 'usage_based',
        name='pricetype'
    )
    
    price_currency = sa.Enum(
        'usd', 'eur', 'gbp', 'cad', 'aud', 'jpy',
        name='pricecurrency'
    )
    
    payment_status = sa.Enum(
        'pending', 'completed', 'failed', 'refunded', 'canceled',
        name='paymentstatus'
    )
    
    payment_method = sa.Enum(
        'credit_card', 'debit_card', 'bank_transfer', 'paypal', 'crypto',
        name='paymentmethod'
    )
    
    invoice_status = sa.Enum(
        'draft', 'open', 'paid', 'void', 'uncollectible',
        name='invoicestatus'
    )
    
    subscription_status = sa.Enum(
        'incomplete', 'incomplete_expired', 'trialing', 'active',
        'past_due', 'canceled', 'unpaid',
        name='subscriptionstatus'
    )
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('tier', customer_tier, nullable=False, server_default='free'),
        sa.Column('default_payment_method_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id')
    )
    op.create_index(op.f('ix_customers_stripe_customer_id'), 'customers', ['stripe_customer_id'], unique=True)
    
    # Create plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stripe_product_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tier', customer_tier, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plans_stripe_product_id'), 'plans', ['stripe_product_id'], unique=True)
    op.create_index(op.f('ix_plans_tier'), 'plans', ['tier'], unique=False)
    
    # Create prices table
    op.create_table(
        'prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', price_currency, nullable=False, server_default='usd'),
        sa.Column('price_type', price_type, nullable=False),
        sa.Column('interval', plan_interval, nullable=True),
        sa.Column('interval_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('trial_period_days', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prices_stripe_price_id'), 'prices', ['stripe_price_id'], unique=True)
    op.create_index(op.f('ix_prices_price_type'), 'prices', ['price_type'], unique=False)
    op.create_index(op.f('ix_prices_interval'), 'prices', ['interval'], unique=False)
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('status', subscription_status, nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, default=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=True)
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)
    
    # Create subscription_items table
    op.create_table(
        'subscription_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('price_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_item_id', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['price_id'], ['prices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_items_stripe_subscription_item_id'), 'subscription_items', ['stripe_subscription_item_id'], unique=True)
    
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(), nullable=True),
        sa.Column('status', invoice_status, nullable=False),
        sa.Column('currency', price_currency, nullable=False, server_default='usd'),
        sa.Column('amount_due', sa.Float(), nullable=False),
        sa.Column('amount_paid', sa.Float(), nullable=False, default=0),
        sa.Column('amount_remaining', sa.Float(), nullable=False),
        sa.Column('invoice_pdf', sa.String(), nullable=True),
        sa.Column('hosted_invoice_url', sa.String(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_stripe_invoice_id'), 'invoices', ['stripe_invoice_id'], unique=True)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)
    
    # Create invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('price_id', sa.Integer(), nullable=True),
        sa.Column('stripe_invoice_item_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', price_currency, nullable=False, server_default='usd'),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.ForeignKeyConstraint(['price_id'], ['prices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_items_stripe_invoice_item_id'), 'invoice_items', ['stripe_invoice_item_id'], unique=True)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
        sa.Column('stripe_charge_id', sa.String(), nullable=True),
        sa.Column('status', payment_status, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', price_currency, nullable=False, server_default='usd'),
        sa.Column('payment_method', payment_method, nullable=True),
        sa.Column('payment_method_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('receipt_url', sa.String(), nullable=True),
        sa.Column('failure_code', sa.String(), nullable=True),
        sa.Column('failure_message', sa.String(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_stripe_payment_intent_id'), 'payments', ['stripe_payment_intent_id'], unique=True)
    op.create_index(op.f('ix_payments_stripe_charge_id'), 'payments', ['stripe_charge_id'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)


def downgrade() -> None:
    # Drop all indexes
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_stripe_charge_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_stripe_payment_intent_id'), table_name='payments')
    
    op.drop_index(op.f('ix_invoice_items_stripe_invoice_item_id'), table_name='invoice_items')
    
    op.drop_index(op.f('ix_invoices_status'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_stripe_invoice_id'), table_name='invoices')
    
    op.drop_index(op.f('ix_subscription_items_stripe_subscription_item_id'), table_name='subscription_items')
    
    op.drop_index(op.f('ix_subscriptions_status'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_stripe_subscription_id'), table_name='subscriptions')
    
    op.drop_index(op.f('ix_prices_interval'), table_name='prices')
    op.drop_index(op.f('ix_prices_price_type'), table_name='prices')
    op.drop_index(op.f('ix_prices_stripe_price_id'), table_name='prices')
    
    op.drop_index(op.f('ix_plans_tier'), table_name='plans')
    op.drop_index(op.f('ix_plans_stripe_product_id'), table_name='plans')
    
    op.drop_index(op.f('ix_customers_stripe_customer_id'), table_name='customers')
    
    # Drop all tables
    op.drop_table('payments')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('subscription_items')
    op.drop_table('subscriptions')
    op.drop_table('prices')
    op.drop_table('plans')
    op.drop_table('customers')
    
    # Drop all enum types
    sa.Enum(name='subscriptionstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='invoicestatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='paymentmethod').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='paymentstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='pricecurrency').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='pricetype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='planinterval').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='customertier').drop(op.get_bind(), checkfirst=False)