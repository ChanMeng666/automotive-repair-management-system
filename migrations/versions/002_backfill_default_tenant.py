"""Create Default Organization and backfill tenant_id, migrate roles

Revision ID: 002
Revises: 001
Create Date: 2026-02-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Default Organization tenant
    op.execute(
        sa.text("""
            INSERT INTO tenant (name, slug, business_type, status, created_at, updated_at)
            VALUES ('Default Organization', 'default-org', 'both', 'active', NOW(), NOW())
        """)
    )

    # Get the default tenant ID (should be 1)
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT tenant_id FROM tenant WHERE slug = 'default-org'"))
    default_tenant_id = result.scalar()

    # Backfill tenant_id on all existing rows
    op.execute(sa.text(f"UPDATE customer SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"))
    op.execute(sa.text(f"UPDATE job SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"))
    op.execute(sa.text(f"UPDATE service SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"))
    op.execute(sa.text(f"UPDATE part SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"))

    # Migrate User.role to TenantMembership
    # Map old roles to new roles: administrator -> owner, technician -> technician
    op.execute(sa.text(f"""
        INSERT INTO tenant_membership (user_id, tenant_id, role, is_default, status, accepted_at, created_at, updated_at)
        SELECT
            user_id,
            {default_tenant_id},
            CASE
                WHEN role = 'administrator' THEN 'owner'
                WHEN role = 'technician' THEN 'technician'
                ELSE 'viewer'
            END,
            true,
            'active',
            NOW(),
            NOW(),
            NOW()
        FROM "user"
        WHERE role IS NOT NULL
    """))

    # Create free subscription for default tenant
    op.execute(sa.text(f"""
        INSERT INTO subscription (tenant_id, plan, status, created_at, updated_at)
        VALUES ({default_tenant_id}, 'free', 'active', NOW(), NOW())
    """))


def downgrade() -> None:
    # Remove memberships and subscription for default tenant
    op.execute(sa.text("DELETE FROM subscription WHERE tenant_id = (SELECT tenant_id FROM tenant WHERE slug = 'default-org')"))
    op.execute(sa.text("DELETE FROM tenant_membership WHERE tenant_id = (SELECT tenant_id FROM tenant WHERE slug = 'default-org')"))

    # Reset tenant_id on existing tables
    op.execute(sa.text("UPDATE customer SET tenant_id = NULL"))
    op.execute(sa.text("UPDATE job SET tenant_id = NULL"))
    op.execute(sa.text("UPDATE service SET tenant_id = NULL"))
    op.execute(sa.text("UPDATE part SET tenant_id = NULL"))

    # Remove default tenant
    op.execute(sa.text("DELETE FROM tenant WHERE slug = 'default-org'"))
