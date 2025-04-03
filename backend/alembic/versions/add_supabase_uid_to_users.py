"""add_supabase_uid_to_users

Revision ID: 6b9cf4b61cf1
Revises: 
Create Date: 2025-04-03 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b9cf4b61cf1'
down_revision = None  # Update this with the previous revision if needed
branch_labels = None
depends_on = None


def upgrade():
    # Add supabase_uid column to users table
    op.add_column('users', sa.Column('supabase_uid', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_supabase_uid'), 'users', ['supabase_uid'], unique=True)


def downgrade():
    # Remove supabase_uid column from users table
    op.drop_index(op.f('ix_users_supabase_uid'), table_name='users')
    op.drop_column('users', 'supabase_uid')