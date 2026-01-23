"""
Job Model - SQLAlchemy ORM
Work orders with services and parts
"""
from typing import List, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Date, Numeric, Boolean, Integer, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.base import BaseModelMixin


class JobService(db.Model):
    """Junction table for Job-Service relationship"""

    __tablename__ = 'job_service'

    job_id: Mapped[int] = mapped_column(ForeignKey('job.job_id', onupdate='CASCADE'), primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey('service.service_id', onupdate='CASCADE'), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_services")
    service: Mapped["Service"] = relationship("Service", back_populates="job_services")

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost for this service entry"""
        return self.service.cost * Decimal(str(self.qty))


class JobPart(db.Model):
    """Junction table for Job-Part relationship"""

    __tablename__ = 'job_part'

    job_id: Mapped[int] = mapped_column(ForeignKey('job.job_id', onupdate='CASCADE'), primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey('part.part_id', onupdate='CASCADE'), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_parts")
    part: Mapped["Part"] = relationship("Part", back_populates="job_parts")

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost for this part entry"""
        return self.part.cost * Decimal(str(self.qty))


class Job(db.Model, BaseModelMixin):
    """Job (Work Order) model class"""

    __tablename__ = 'job'

    job_id: Mapped[int] = mapped_column(primary_key=True)
    job_date: Mapped[date] = mapped_column(Date, nullable=False)
    customer: Mapped[int] = mapped_column(ForeignKey('customer.customer_id', onupdate='CASCADE'), nullable=False)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    customer_rel: Mapped["Customer"] = relationship("Customer", back_populates="jobs")
    job_services: Mapped[List["JobService"]] = relationship("JobService", back_populates="job", cascade="all, delete-orphan")
    job_parts: Mapped[List["JobPart"]] = relationship("JobPart", back_populates="job", cascade="all, delete-orphan")

    @classmethod
    def get_current_jobs(cls, page: int = 1, per_page: int = 10) -> Tuple[List['Job'], int]:
        """
        Get current incomplete jobs with pagination

        Returns:
            Tuple of (jobs list, total count)
        """
        from app.models.customer import Customer

        # Get total count
        total = db.session.execute(
            db.select(db.func.count()).select_from(cls).where(cls.completed == False)
        ).scalar() or 0

        # Get paginated results
        offset = (page - 1) * per_page
        query = db.select(cls).where(cls.completed == False).join(
            Customer, cls.customer == Customer.customer_id
        ).order_by(Customer.first_name, Customer.family_name, cls.job_date.desc()).offset(offset).limit(per_page)

        jobs = list(db.session.execute(query).scalars())
        return jobs, total

    @classmethod
    def get_all_with_customer_info(cls) -> List['Job']:
        """Get all jobs with customer information loaded"""
        from app.models.customer import Customer
        query = db.select(cls).join(Customer).order_by(cls.job_date.desc())
        return list(db.session.execute(query).scalars())

    @classmethod
    def get_unpaid_jobs(cls, customer_name: Optional[str] = None) -> List['Job']:
        """Get unpaid jobs, optionally filtered by customer name"""
        from app.models.customer import Customer

        query = db.select(cls).join(Customer).where(cls.paid == False)

        if customer_name and customer_name != 'Choose...':
            full_name_expr = db.func.concat(
                db.func.coalesce(Customer.first_name, ''), ' ', Customer.family_name
            )
            query = query.where(full_name_expr == customer_name)

        query = query.order_by(Customer.family_name, Customer.first_name, cls.job_date)
        return list(db.session.execute(query).scalars())

    @classmethod
    def get_overdue_jobs(cls, days_threshold: int = 14) -> List['Job']:
        """Get overdue jobs (unpaid and past threshold)"""
        from app.models.customer import Customer

        threshold_date = date.today() - __import__('datetime').timedelta(days=days_threshold)
        query = db.select(cls).join(Customer).where(
            and_(cls.paid == False, cls.job_date < threshold_date)
        ).order_by(cls.job_date.asc())

        return list(db.session.execute(query).scalars())

    def get_services(self) -> List[dict]:
        """Get services for this job"""
        return [
            {
                'service_name': js.service.service_name,
                'qty': js.qty,
                'cost': float(js.service.cost),
                'total_cost': float(js.total_cost)
            }
            for js in self.job_services
        ]

    def get_parts(self) -> List[dict]:
        """Get parts for this job"""
        return [
            {
                'part_name': jp.part.part_name,
                'qty': jp.qty,
                'cost': float(jp.part.cost),
                'total_cost': float(jp.total_cost)
            }
            for jp in self.job_parts
        ]

    def add_service(self, service_id: int, quantity: int) -> bool:
        """Add a service to this job"""
        if self.completed:
            raise ValueError("Cannot modify a completed job")

        from app.models.service import Service
        service = Service.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        job_service = JobService(job_id=self.job_id, service_id=service_id, qty=quantity)
        db.session.add(job_service)
        self._update_total_cost()
        db.session.commit()
        return True

    def add_part(self, part_id: int, quantity: int) -> bool:
        """Add a part to this job"""
        if self.completed:
            raise ValueError("Cannot modify a completed job")

        from app.models.part import Part
        part = Part.find_by_id(part_id)
        if not part:
            raise ValueError(f"Part {part_id} not found")

        job_part = JobPart(job_id=self.job_id, part_id=part_id, qty=quantity)
        db.session.add(job_part)
        self._update_total_cost()
        db.session.commit()
        return True

    def mark_as_completed(self) -> bool:
        """Mark job as completed"""
        self.completed = True
        db.session.commit()
        return True

    def mark_as_paid(self) -> bool:
        """Mark job as paid"""
        self.paid = True
        db.session.commit()
        return True

    def _update_total_cost(self) -> None:
        """Recalculate and update total cost"""
        service_total = sum(js.total_cost for js in self.job_services)
        part_total = sum(jp.total_cost for jp in self.job_parts)
        self.total_cost = service_total + part_total

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if job is overdue (14 days threshold)"""
        if self.paid or not self.job_date:
            return False
        days_diff = (date.today() - self.job_date).days
        return days_diff > 14

    @property
    def status_text(self) -> str:
        """Get status text"""
        if self.completed and self.paid:
            return "Completed & Paid"
        elif self.completed:
            return "Completed - Unpaid"
        else:
            return "In Progress"

    @property
    def days_since_job(self) -> int:
        """Days since job was created"""
        if not self.job_date:
            return 0
        return (date.today() - self.job_date).days

    def to_dict(self) -> dict:
        """Convert to dictionary with computed fields"""
        data = super().to_dict()
        data['is_overdue'] = self.is_overdue
        data['status_text'] = self.status_text
        data['days_since_job'] = self.days_since_job
        if self.total_cost:
            data['total_cost'] = float(self.total_cost)
        # Include customer info if loaded
        if self.customer_rel:
            data['first_name'] = self.customer_rel.first_name
            data['family_name'] = self.customer_rel.family_name
            data['customer_id'] = self.customer_rel.customer_id
        return data


# Import for type hints
from app.models.customer import Customer
from app.models.service import Service
from app.models.part import Part
