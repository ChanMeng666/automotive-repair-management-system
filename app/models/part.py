"""
Part Model - SQLAlchemy ORM
Multi-tenant parts catalog
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin, TenantScopedMixin


class Part(db.Model, BaseModelMixin, TenantScopedMixin):
    """Part model class"""

    __tablename__ = 'part'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'sku', name='uq_part_tenant_sku'),
    )

    part_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True
    )
    part_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    job_parts: Mapped[List["JobPart"]] = relationship("JobPart", back_populates="part")
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", backref="parts")

    @classmethod
    def get_all_sorted(cls) -> List['Part']:
        """Get all parts sorted by name, scoped to tenant"""
        query = db.select(cls)
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.part_name)
        return list(db.session.execute(query).scalars())

    @classmethod
    def get_active_sorted(cls) -> List['Part']:
        """Get active parts sorted by name, scoped to tenant"""
        query = db.select(cls).where(cls.is_active == True)
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.part_name)
        return list(db.session.execute(query).scalars())

    @classmethod
    def search_by_name(cls, search_term: str) -> List['Part']:
        """Search parts by name"""
        search_pattern = f"%{search_term}%"
        query = db.select(cls).where(cls.part_name.ilike(search_pattern))
        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)
        query = query.order_by(cls.part_name)
        return list(db.session.execute(query).scalars())

    def calculate_total_cost(self, quantity: int) -> Decimal:
        """Calculate total cost for given quantity"""
        if not self.cost or quantity <= 0:
            return Decimal('0')
        return self.cost * Decimal(str(quantity))

    def get_usage_statistics(self) -> dict:
        """Get part usage statistics"""
        from app.models.job import JobPart

        result = db.session.execute(
            db.select(
                db.func.count(JobPart.job_id).label('usage_count'),
                db.func.coalesce(db.func.sum(JobPart.qty), 0).label('total_quantity'),
                db.func.coalesce(db.func.sum(JobPart.qty * self.cost), 0).label('total_cost')
            ).where(JobPart.part_id == self.part_id)
        ).one()

        return {
            'usage_count': result.usage_count,
            'total_quantity': int(result.total_quantity),
            'total_cost': float(result.total_cost)
        }

    @classmethod
    def get_inventory_report(cls) -> List[dict]:
        """Get inventory report with usage statistics"""
        from app.models.job import JobPart

        query = db.select(
            cls.part_id,
            cls.part_name,
            cls.cost,
            db.func.count(JobPart.job_id).label('usage_count'),
            db.func.coalesce(db.func.sum(JobPart.qty), 0).label('total_used'),
            db.func.coalesce(db.func.sum(JobPart.qty * cls.cost), 0).label('total_value')
        ).outerjoin(JobPart).group_by(cls.part_id, cls.part_name, cls.cost)

        tenant_id = cls._get_current_tenant_id()
        if tenant_id:
            query = query.where(cls.tenant_id == tenant_id)

        query = query.order_by(db.desc('usage_count'), cls.part_name)

        results = db.session.execute(query).all()
        return [
            {
                'part_id': r.part_id,
                'part_name': r.part_name,
                'cost': float(r.cost),
                'usage_count': r.usage_count,
                'total_used': int(r.total_used),
                'total_value': float(r.total_value)
            }
            for r in results
        ]

    def validate(self) -> List[str]:
        """Validate part data"""
        errors = []

        if not self.part_name or not self.part_name.strip():
            errors.append("Part name is required")

        if self.cost is None:
            errors.append("Part cost is required")
        elif self.cost < 0:
            errors.append("Part cost cannot be negative")

        return errors

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        if self.cost:
            data['cost'] = float(self.cost)
        return data

    def __str__(self) -> str:
        return f"{self.part_name} (${self.cost})"


# Import for type hints
from app.models.job import JobPart
