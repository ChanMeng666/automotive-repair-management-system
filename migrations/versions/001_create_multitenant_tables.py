"""Create multi-tenant tables and add tenant_id to existing tables

Revision ID: 001
Revises: None
Create Date: 2026-02-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenant table
    op.create_table(
        'tenant',
        sa.Column('tenant_id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('business_type', sa.String(20), nullable=False, server_default='auto_repair'),
        sa.Column('email', sa.String(320), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='trial'),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_tenant_slug', 'tenant', ['slug'])

    # Create tenant_membership table
    op.create_table(
        'tenant_membership',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.user_id'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('invited_by', sa.Integer(), sa.ForeignKey('user.user_id'), nullable=True),
        sa.Column('invited_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
    )

    # Create subscription table
    op.create_table(
        'subscription',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=False, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('status', sa.String(20), nullable=False, server_default='trialing'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('inventory_id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=False),
        sa.Column('part_id', sa.Integer(), sa.ForeignKey('part.part_id'), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_inventory_tenant_id', 'inventory', ['tenant_id'])

    # Create inventory_transaction table
    op.create_table(
        'inventory_transaction',
        sa.Column('transaction_id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=False),
        sa.Column('inventory_id', sa.Integer(), sa.ForeignKey('inventory.inventory_id'), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('performed_by', sa.Integer(), sa.ForeignKey('user.user_id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_inventory_transaction_tenant_id', 'inventory_transaction', ['tenant_id'])

    # Add is_superadmin to user table
    op.add_column('user', sa.Column('is_superadmin', sa.Boolean(), server_default='false'))

    # Add nullable tenant_id to existing tables
    op.add_column('customer', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=True))
    op.create_index('ix_customer_tenant_id', 'customer', ['tenant_id'])

    op.add_column('job', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=True))
    op.add_column('job', sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('user.user_id'), nullable=True))
    op.create_index('ix_job_tenant_id', 'job', ['tenant_id'])

    op.add_column('service', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=True))
    op.add_column('service', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('service', sa.Column('category', sa.String(50), nullable=True))
    op.add_column('service', sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('service', sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.create_index('ix_service_tenant_id', 'service', ['tenant_id'])

    op.add_column('part', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.tenant_id'), nullable=True))
    op.add_column('part', sa.Column('sku', sa.String(50), nullable=True))
    op.add_column('part', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('part', sa.Column('category', sa.String(50), nullable=True))
    op.add_column('part', sa.Column('supplier', sa.String(100), nullable=True))
    op.add_column('part', sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.create_index('ix_part_tenant_id', 'part', ['tenant_id'])

    # Widen service_name and part_name columns
    op.alter_column('service', 'service_name', type_=sa.String(100))
    op.alter_column('part', 'part_name', type_=sa.String(100))


def downgrade() -> None:
    # Remove added columns from existing tables
    op.drop_index('ix_part_tenant_id', 'part')
    op.drop_column('part', 'is_active')
    op.drop_column('part', 'supplier')
    op.drop_column('part', 'category')
    op.drop_column('part', 'description')
    op.drop_column('part', 'sku')
    op.drop_column('part', 'tenant_id')

    op.drop_index('ix_service_tenant_id', 'service')
    op.drop_column('service', 'is_active')
    op.drop_column('service', 'estimated_duration_minutes')
    op.drop_column('service', 'category')
    op.drop_column('service', 'description')
    op.drop_column('service', 'tenant_id')

    op.drop_index('ix_job_tenant_id', 'job')
    op.drop_column('job', 'assigned_to')
    op.drop_column('job', 'tenant_id')

    op.drop_index('ix_customer_tenant_id', 'customer')
    op.drop_column('customer', 'tenant_id')

    op.drop_column('user', 'is_superadmin')

    # Drop new tables
    op.drop_table('inventory_transaction')
    op.drop_table('inventory')
    op.drop_table('subscription')
    op.drop_table('tenant_membership')
    op.drop_table('tenant')
