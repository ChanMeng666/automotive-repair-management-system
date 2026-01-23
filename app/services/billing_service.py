"""
Billing Service
Business logic for billing and payment operations using SQLAlchemy ORM
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import logging
from app.extensions import db
from app.models.job import Job
from app.models.customer import Customer


class BillingService:
    """Billing service class"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_unpaid_bills(self, customer_name: Optional[str] = None) -> List[Job]:
        """
        Get unpaid bills

        Args:
            customer_name: Customer name filter (optional)

        Returns:
            List of unpaid jobs
        """
        try:
            return Job.get_unpaid_jobs(customer_name)
        except Exception as e:
            self.logger.error(f"Failed to get unpaid bills: {e}")
            return []

    def get_overdue_bills(self, days_threshold: int = 14) -> List[Job]:
        """
        Get overdue bills

        Args:
            days_threshold: Overdue days threshold

        Returns:
            List of overdue jobs
        """
        try:
            return Job.get_overdue_jobs(days_threshold)
        except Exception as e:
            self.logger.error(f"Failed to get overdue bills: {e}")
            return []

    def get_all_bills_with_status(self) -> List[Dict[str, Any]]:
        """Get all bills with status information"""
        try:
            jobs = Job.get_all_with_customer_info()

            bills = []
            for job in jobs:
                bill = job.to_dict()
                bill['overdue'] = job.is_overdue
                bill['days_overdue'] = job.days_since_job if job.is_overdue else 0
                bills.append(bill)

            return bills

        except Exception as e:
            self.logger.error(f"Failed to get all bills: {e}")
            return []

    def mark_customer_bills_as_paid(self, customer_id: int) -> Tuple[bool, List[str], int]:
        """
        Mark all unpaid bills for a customer as paid

        Args:
            customer_id: Customer ID

        Returns:
            (success, error_messages, count_marked)
        """
        try:
            customer = Customer.find_by_id(customer_id)
            if not customer:
                return False, ["Customer does not exist"], 0

            unpaid_jobs = customer.get_unpaid_jobs()
            if not unpaid_jobs:
                return False, ["This customer has no unpaid bills"], 0

            count = 0
            for job in unpaid_jobs:
                job.paid = True
                count += 1

            db.session.commit()
            self.logger.info(f"Marked {count} bills as paid for customer {customer.full_name}")
            return True, [], count

        except Exception as e:
            self.logger.error(f"Failed to mark customer bills as paid: {e}")
            db.session.rollback()
            return False, ["System error, please try again"], 0

    def mark_job_as_paid(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        Mark a single job as paid

        Args:
            job_id: Job ID

        Returns:
            (success, error_messages)
        """
        try:
            job = Job.find_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.paid:
                return False, ["Bill is already paid"]

            job.mark_as_paid()
            self.logger.info(f"Job {job_id} marked as paid")
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to mark bill as paid: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def get_customer_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """
        Get customer billing summary

        Args:
            customer_id: Customer ID

        Returns:
            Customer billing summary
        """
        try:
            customer = Customer.find_by_id(customer_id)
            if not customer:
                return {}

            all_jobs = customer.get_jobs()
            unpaid_jobs = customer.get_unpaid_jobs()

            total_amount = sum(float(job.total_cost or 0) for job in all_jobs)
            unpaid_amount = sum(float(job.total_cost or 0) for job in unpaid_jobs)
            paid_amount = total_amount - unpaid_amount

            overdue_jobs = [job for job in unpaid_jobs if job.is_overdue]
            overdue_amount = sum(float(job.total_cost or 0) for job in overdue_jobs)

            return {
                'customer_info': customer.to_dict(),
                'total_jobs': len(all_jobs),
                'total_amount': total_amount,
                'paid_jobs': len(all_jobs) - len(unpaid_jobs),
                'paid_amount': paid_amount,
                'unpaid_jobs': len(unpaid_jobs),
                'unpaid_amount': unpaid_amount,
                'overdue_jobs': len(overdue_jobs),
                'overdue_amount': overdue_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get customer billing summary: {e}")
            return {}

    def get_billing_statistics(self) -> Dict[str, Any]:
        """Get overall billing statistics"""
        try:
            # Get all jobs with costs
            query = db.select(
                db.func.count(Job.job_id).label('total_bills'),
                db.func.coalesce(db.func.sum(Job.total_cost), 0).label('total_amount'),
                db.func.count(db.case((Job.paid == True, 1))).label('paid_bills'),
                db.func.coalesce(db.func.sum(db.case((Job.paid == True, Job.total_cost), else_=0)), 0).label('paid_amount'),
                db.func.count(db.case((Job.paid == False, 1))).label('unpaid_bills'),
                db.func.coalesce(db.func.sum(db.case((Job.paid == False, Job.total_cost), else_=0)), 0).label('unpaid_amount')
            ).where(Job.total_cost > 0)

            result = db.session.execute(query).one()

            overdue_bills = self.get_overdue_bills()
            overdue_amount = sum(float(job.total_cost or 0) for job in overdue_bills)

            total_amount = float(result.total_amount)
            paid_amount = float(result.paid_amount)

            return {
                'total_bills': result.total_bills,
                'total_amount': total_amount,
                'paid_bills': result.paid_bills,
                'paid_amount': paid_amount,
                'unpaid_bills': result.unpaid_bills,
                'unpaid_amount': float(result.unpaid_amount),
                'overdue_bills': len(overdue_bills),
                'overdue_amount': overdue_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get billing statistics: {e}")
            return self._get_empty_billing_stats()

    def get_customers_with_unpaid_bills(self) -> List[Dict[str, Any]]:
        """Get customers with unpaid bills"""
        try:
            query = db.select(
                Customer.customer_id,
                Customer.first_name,
                Customer.family_name,
                Customer.email,
                Customer.phone,
                db.func.count(Job.job_id).label('unpaid_count'),
                db.func.coalesce(db.func.sum(Job.total_cost), 0).label('unpaid_amount')
            ).join(Job).where(Job.paid == False).group_by(
                Customer.customer_id,
                Customer.first_name,
                Customer.family_name,
                Customer.email,
                Customer.phone
            ).order_by(db.desc('unpaid_amount'), Customer.family_name, Customer.first_name)

            results = db.session.execute(query).all()

            return [
                {
                    'customer_id': r.customer_id,
                    'first_name': r.first_name,
                    'family_name': r.family_name,
                    'email': r.email,
                    'phone': r.phone,
                    'unpaid_count': r.unpaid_count,
                    'unpaid_amount': float(r.unpaid_amount)
                }
                for r in results
            ]

        except Exception as e:
            self.logger.error(f"Failed to get customers with unpaid bills: {e}")
            return []

    def _get_empty_billing_stats(self) -> Dict[str, Any]:
        """Return empty billing statistics"""
        return {
            'total_bills': 0,
            'total_amount': 0.0,
            'paid_bills': 0,
            'paid_amount': 0.0,
            'unpaid_bills': 0,
            'unpaid_amount': 0.0,
            'overdue_bills': 0,
            'overdue_amount': 0.0,
            'payment_rate': 0.0
        }
