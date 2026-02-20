"""
Subscription Model - Stripe integration
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin


class Subscription(db.Model, BaseModelMixin, TimestampMixin):
    """Tracks tenant subscription and Stripe billing"""

    __tablename__ = 'subscription'

    # Plan constants
    PLAN_FREE = 'free'
    PLAN_STARTER = 'starter'
    PLAN_PROFESSIONAL = 'professional'
    PLAN_ENTERPRISE = 'enterprise'
    VALID_PLANS = [PLAN_FREE, PLAN_STARTER, PLAN_PROFESSIONAL, PLAN_ENTERPRISE]

    # Status constants
    STATUS_TRIALING = 'trialing'
    STATUS_ACTIVE = 'active'
    STATUS_PAST_DUE = 'past_due'
    STATUS_CANCELED = 'canceled'
    VALID_STATUSES = [STATUS_TRIALING, STATUS_ACTIVE, STATUS_PAST_DUE, STATUS_CANCELED]

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=False, unique=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default=PLAN_FREE)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=STATUS_TRIALING
    )
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        """Check if subscription allows access"""
        return self.status in (self.STATUS_TRIALING, self.STATUS_ACTIVE)

    def __repr__(self) -> str:
        return f"<Subscription tenant={self.tenant_id} plan={self.plan} status={self.status}>"
