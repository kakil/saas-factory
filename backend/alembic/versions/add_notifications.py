"""Add notifications tables

Revision ID: 4c8d0a57d9b6
Revises: 3b9d0a47c9a5
Create Date: 2025-04-04 16:30:21.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4c8d0a57d9b6'
down_revision: str = '3b9d0a47c9a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum types 
    notification_type = sa.Enum(
        'system', 'activity', 'alert', 'billing', 'team', 'welcome', 'security',
        name='notificationtype'
    )
    notification_channel = sa.Enum(
        'in_app', 'email', 'sms', 'push', 'webhook',
        name='notificationchannel'
    )
    
    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(), nullable=False),
        sa.Column('channels', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'notification_type')
    )
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', notification_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('channel', notification_channel, nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_delivered', sa.Boolean(), nullable=False, default=False),
        sa.Column('action_url', sa.String(), nullable=True),
        sa.Column('action_text', sa.String(), nullable=True),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_organization_id'), 'notifications', ['organization_id'], unique=False)
    op.create_index(op.f('ix_notifications_channel'), 'notifications', ['channel'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_notifications_channel'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_organization_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    
    # Drop tables
    op.drop_table('notifications')
    op.drop_table('notification_preferences')
    
    # Drop enum types
    sa.Enum(name='notificationchannel').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=False)