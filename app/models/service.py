"""
Service Model - SQLAlchemy ORM
Multi-tenant service catalog
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey, Boolean, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TenantScopedMixin


class Service(db.Model, BaseModelMixin, TenantScopedMixin):
    """Service model class"""

    __tablename__ = 'service'

    service_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    job_services: Mapped[List["JobService"]] = relationship("JobService", back_populates="service")
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", backref="services")

    @classmethod
    def get_all_sorted(cls) -> List['Service']:
        """Get all services sorted by name, scoped to tenant"""
        query = db.select(cls)
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.service_name)
        return list(db.session.execute(query).scalars())

    @classmethod
    def get_active_sorted(cls) -> List['Service']:
        """Get active services sorted by name, scoped to tenant"""
        query = db.select(cls).where(cls.is_active == True)
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.service_name)
        return list(db.session.execute(query).scalars())

    @classmethod
    def search_by_name(cls, search_term: str) -> List['Service']:
        """Search services by name"""
        search_pattern = f"%{search_term}%"
        query = db.select(cls).where(cls.service_name.ilike(search_pattern))
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.service_name)
        return list(db.session.execute(query).scalars())

    def calculate_total_cost(self, quantity: int) -> Decimal:
        """Calculate total cost for given quantity"""
        if not self.cost or quantity <= 0:
            return Decimal('0')
        return self.cost * Decimal(str(quantity))

    def get_usage_statistics(self) -> dict:
        """Get service usage statistics"""
        from app.models.job import JobService

        result = db.session.execute(
            db.select(
                db.func.count(JobService.job_id).label('usage_count'),
                db.func.coalesce(db.func.sum(JobService.qty), 0).label('total_quantity'),
                db.func.coalesce(db.func.sum(JobService.qty * self.cost), 0).label('total_revenue')
            ).where(JobService.service_id == self.service_id)
        ).one()

        return {
            'usage_count': result.usage_count,
            'total_quantity': int(result.total_quantity),
            'total_revenue': float(result.total_revenue)
        }

    def validate(self) -> List[str]:
        """Validate service data"""
        errors = []

        if not self.service_name or not self.service_name.strip():
            errors.append("Service name is required")

        if self.cost is None:
            errors.append("Service cost is required")
        elif self.cost < 0:
            errors.append("Service cost cannot be negative")

        return errors

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        if self.cost:
            data['cost'] = float(self.cost)
        return data

    def __str__(self) -> str:
        return f"{self.service_name} (${self.cost})"


# Import for type hints
from app.models.job import JobService
