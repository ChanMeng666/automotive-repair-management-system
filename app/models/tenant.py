"""
Tenant Model - Multi-tenant organization
"""
import re
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin


class Tenant(db.Model, BaseModelMixin, TimestampMixin):
    """Tenant model for multi-tenant organizations"""

    __tablename__ = 'tenant'

    # Business type constants
    TYPE_AUTO_REPAIR = 'auto_repair'
    TYPE_PARTS_SELLER = 'parts_seller'
    TYPE_BOTH = 'both'
    VALID_TYPES = [TYPE_AUTO_REPAIR, TYPE_PARTS_SELLER, TYPE_BOTH]

    # Status constants
    STATUS_TRIAL = 'trial'
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    VALID_STATUSES = [STATUS_TRIAL, STATUS_ACTIVE, STATUS_SUSPENDED]

    tenant_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    business_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TYPE_AUTO_REPAIR
    )
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_TRIAL)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships - use backref from child models (customer.py, job.py, etc.)
    memberships: Mapped[List["TenantMembership"]] = relationship(
        "TenantMembership", back_populates="tenant", lazy="dynamic"
    )
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="tenant", uselist=False
    )

    @classmethod
    def find_by_slug(cls, slug: str) -> Optional['Tenant']:
        """Find tenant by URL slug"""
        query = db.select(cls).where(cls.slug == slug)
        return db.session.execute(query).scalar_one_or_none()

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-friendly slug from tenant name"""
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while Tenant.find_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['settings'] = self.settings or {}
        return data

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.slug})>"
