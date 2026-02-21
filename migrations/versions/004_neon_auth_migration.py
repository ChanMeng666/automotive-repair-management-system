"""Neon Auth migration: nullable password_hash, add email_verified

Revision ID: 004
Revises: 003
Create Date: 2026-02-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Make password_hash nullable (Neon Auth users don't have local passwords)
    op.alter_column('user', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)

    # Add email_verified column
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('user', 'email_verified')
    op.alter_column('user', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)
