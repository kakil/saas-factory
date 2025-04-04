"""add_tenant_rls

Revision ID: 2fbd9033a2af
Revises: 6b9cf4b61cf1
Create Date: 2025-04-04 10:26:29.212856

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '2fbd9033a2af'
down_revision = '6b9cf4b61cf1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create app schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS app')
    
    # Create tenant_context function to get current tenant
    op.execute("""
    CREATE OR REPLACE FUNCTION app.current_tenant_id()
    RETURNS INTEGER AS $$
    DECLARE
        tenant INTEGER;
    BEGIN
        tenant = current_setting('app.current_tenant', TRUE);
        IF tenant IS NULL THEN
            RETURN NULL;
        END IF;
        RETURN tenant::INTEGER;
    EXCEPTION
        WHEN OTHERS THEN
            RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Enable RLS on tenant-specific tables
    tables = ['users', 'teams', 'user_team']
    
    for table in tables:
        # Enable row level security
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Create policy for superusers to bypass RLS
        op.execute(f"""
        CREATE POLICY admin_policy ON {table}
        USING (EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = current_user::INTEGER 
            AND users.is_superuser = TRUE
        ));
        """)

    # Create RLS policies for users table
    op.execute("""
    CREATE POLICY tenant_isolation_policy ON users
    USING (
        (app.current_tenant_id() IS NULL) OR -- No tenant context
        (organization_id = app.current_tenant_id()) OR -- User belongs to current tenant
        (organization_id IS NULL) -- User not assigned to an organization
    );
    """)
    
    # Create RLS policies for teams table
    op.execute("""
    CREATE POLICY tenant_isolation_policy ON teams
    USING (
        (app.current_tenant_id() IS NULL) OR -- No tenant context
        (organization_id = app.current_tenant_id()) -- Team belongs to current tenant
    );
    """)
    
    # Create RLS policy for user_team junction table
    op.execute("""
    CREATE POLICY tenant_isolation_policy ON user_team
    USING (
        (app.current_tenant_id() IS NULL) OR -- No tenant context
        (EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = user_team.team_id
            AND teams.organization_id = app.current_tenant_id()
        ))
    );
    """)


def downgrade() -> None:
    # Disable RLS on tenant-specific tables
    tables = ['users', 'teams', 'user_team']
    
    for table in tables:
        # Drop policies
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_policy ON {table}")
        
        # Disable row level security
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    
    # Drop the tenant context function
    op.execute("DROP FUNCTION IF EXISTS app.current_tenant_id()")