"""
Customer Model - SQLAlchemy ORM
"""
from typing import List, Optional
import re
from sqlalchemy import String, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin


class Customer(db.Model, BaseModelMixin):
    """Customer model class"""

    __tablename__ = 'customer'

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    family_name: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(11), nullable=False)

    # Relationships
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="customer_rel", lazy="dynamic")

    @property
    def full_name(self) -> str:
        """Get full name"""
        first = self.first_name or ''
        family = self.family_name or ''
        return f"{first} {family}".strip()

    @classmethod
    def search_by_name(cls, search_term: str, search_type: str = 'both') -> List['Customer']:
        """
        Search customers by name

        Args:
            search_term: Search term
            search_type: Search type ('first_name', 'family_name', 'both')

        Returns:
            List of matching customers
        """
        search_pattern = f"%{search_term}%"

        if search_type == 'first_name':
            query = db.select(cls).where(
                cls.first_name.ilike(search_pattern)
            ).order_by(cls.family_name, cls.first_name)
        elif search_type == 'family_name':
            query = db.select(cls).where(
                cls.family_name.ilike(search_pattern)
            ).order_by(cls.family_name, cls.first_name)
        else:  # both
            query = db.select(cls).where(
                db.or_(
                    cls.first_name.ilike(search_pattern),
                    cls.family_name.ilike(search_pattern)
                )
            ).order_by(cls.family_name, cls.first_name)

        return list(db.session.execute(query).scalars())

    @classmethod
    def get_all_sorted(cls) -> List['Customer']:
        """Get all customers, sorted by name"""
        query = db.select(cls).order_by(cls.family_name, cls.first_name)
        return list(db.session.execute(query).scalars())

    def get_jobs(self, completed_only: bool = False) -> List["Job"]:
        """Get customer's work orders"""
        from app.models.job import Job
        query = self.jobs
        if completed_only:
            query = query.filter(Job.completed == True)
        return query.order_by(Job.job_date.desc()).all()

    def get_unpaid_jobs(self) -> List["Job"]:
        """Get customer's unpaid orders"""
        from app.models.job import Job
        return self.jobs.filter(Job.paid == False).order_by(Job.job_date.asc()).all()

    def get_total_unpaid_amount(self) -> float:
        """Get customer's total unpaid amount"""
        from app.models.job import Job
        result = db.session.execute(
            db.select(db.func.coalesce(db.func.sum(Job.total_cost), 0))
            .where(and_(Job.customer == self.customer_id, Job.paid == False))
        ).scalar()
        return float(result or 0)

    def validate(self) -> List[str]:
        """Validate customer data"""
        errors = []

        if not self.family_name or not self.family_name.strip():
            errors.append("Family name is required")

        if not self.email or not self.email.strip():
            errors.append("Email is required")
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                errors.append(f"Invalid email format: {self.email}")

        if not self.phone or not self.phone.strip():
            errors.append("Phone number is required")

        return errors

    def to_dict(self):
        """Convert to dictionary with computed fields"""
        data = super().to_dict()
        data['full_name'] = self.full_name
        return data


# Import Job here to avoid circular imports - needed for type hints
from app.models.job import Job
