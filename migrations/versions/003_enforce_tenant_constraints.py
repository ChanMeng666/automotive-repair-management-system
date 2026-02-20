"""Set tenant_id NOT NULL, add constraints

Revision ID: 003
Revises: 002
Create Date: 2026-02-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make tenant_id NOT NULL on all tables (data already backfilled)
    op.alter_column('customer', 'tenant_id', nullable=False)
    op.alter_column('job', 'tenant_id', nullable=False)
    op.alter_column('service', 'tenant_id', nullable=False)
    op.alter_column('part', 'tenant_id', nullable=False)

    # Add unique constraints
    op.create_unique_constraint('uq_customer_tenant_email', 'customer', ['tenant_id', 'email'])
    op.create_unique_constraint('uq_part_tenant_sku', 'part', ['tenant_id', 'sku'])


def downgrade() -> None:
    # Drop unique constraints
    op.drop_constraint('uq_part_tenant_sku', 'part')
    op.drop_constraint('uq_customer_tenant_email', 'customer')

    # Make tenant_id nullable again
    op.alter_column('part', 'tenant_id', nullable=True)
    op.alter_column('service', 'tenant_id', nullable=True)
    op.alter_column('job', 'tenant_id', nullable=True)
    op.alter_column('customer', 'tenant_id', nullable=True)
