"""
Tenant Membership - User-Tenant relationship with roles
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin


class TenantMembership(db.Model, BaseModelMixin, TimestampMixin):
    """Maps users to tenants with role-based access"""

    __tablename__ = 'tenant_membership'

    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
    )

    # Role constants
    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_TECHNICIAN = 'technician'
    ROLE_PARTS_CLERK = 'parts_clerk'
    ROLE_VIEWER = 'viewer'
    VALID_ROLES = [
        ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER,
        ROLE_TECHNICIAN, ROLE_PARTS_CLERK, ROLE_VIEWER,
    ]

    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    VALID_STATUSES = [STATUS_PENDING, STATUS_ACTIVE, STATUS_SUSPENDED]

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.user_id'), nullable=False
    )
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=ROLE_VIEWER)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('user.user_id'), nullable=True
    )
    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=STATUS_PENDING
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="memberships"
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="memberships"
    )
    inviter: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[invited_by]
    )

    def __repr__(self) -> str:
        return f"<TenantMembership user={self.user_id} tenant={self.tenant_id} role={self.role}>"
