"""
Customer Service
Business logic for customer operations using SQLAlchemy ORM
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import logging
from app.extensions import db
from app.models.customer import Customer
from app.models.job import Job


class CustomerService:
    """Customer service class"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_all_customers(self, sorted_by_name: bool = True) -> List[Customer]:
        """
        Get all customers

        Args:
            sorted_by_name: Whether to sort by name

        Returns:
            List of customers
        """
        try:
            if sorted_by_name:
                return Customer.get_all_sorted()
            else:
                return Customer.find_all()
        except Exception as e:
            self.logger.error(f"Failed to get customer list: {e}")
            raise

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            return Customer.find_by_id(customer_id)
        except Exception as e:
            self.logger.error(f"Failed to get customer (ID: {customer_id}): {e}")
            raise

    def search_customers(self, search_term: str, search_type: str = 'both') -> List[Customer]:
        """
        Search customers

        Args:
            search_term: Search keyword
            search_type: Search type ('first_name', 'family_name', 'both')

        Returns:
            List of matching customers
        """
        try:
            if not search_term or not search_term.strip():
                return self.get_all_customers()

            return Customer.search_by_name(search_term.strip(), search_type)
        except Exception as e:
            self.logger.error(f"Failed to search customers: {e}")
            raise

    def create_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Customer]]:
        """
        Create a new customer

        Args:
            customer_data: Customer data dictionary

        Returns:
            (success, error_messages, customer)
        """
        try:
            customer = Customer(**customer_data)

            # Validate data
            validation_errors = customer.validate()
            if validation_errors:
                return False, validation_errors, None

            # Save customer
            customer.save()
            self.logger.info(f"Customer created: {customer.full_name}")
            return True, [], customer

        except ValueError as e:
            return False, [str(e)], None
        except Exception as e:
            self.logger.error(f"Failed to create customer: {e}")
            db.session.rollback()
            return False, ["System error, please try again"], None

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Customer]]:
        """
        Update customer information

        Args:
            customer_id: Customer ID
            customer_data: Updated customer data

        Returns:
            (success, error_messages, customer)
        """
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["Customer does not exist"], None

            # Update attributes
            for key, value in customer_data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)

            # Validate data
            validation_errors = customer.validate()
            if validation_errors:
                db.session.rollback()
                return False, validation_errors, None

            # Save updates
            db.session.commit()
            self.logger.info(f"Customer updated: {customer.full_name}")
            return True, [], customer

        except Exception as e:
            self.logger.error(f"Failed to update customer (ID: {customer_id}): {e}")
            db.session.rollback()
            return False, ["System error, please try again"], None

    def delete_customer(self, customer_id: int) -> Tuple[bool, List[str]]:
        """
        Delete customer

        Args:
            customer_id: Customer ID

        Returns:
            (success, error_messages)
        """
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["Customer does not exist"]

            # Check for associated jobs
            jobs = customer.get_jobs()
            if jobs:
                return False, ["Cannot delete customer with work orders"]

            # Delete customer
            customer.delete()
            self.logger.info(f"Customer deleted: {customer.full_name}")
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to delete customer (ID: {customer_id}): {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def get_customer_jobs(self, customer_id: int, completed_only: bool = False) -> List[Job]:
        """Get customer's work orders"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return []

            return customer.get_jobs(completed_only)
        except Exception as e:
            self.logger.error(f"Failed to get customer jobs (ID: {customer_id}): {e}")
            return []

    def get_customer_unpaid_jobs(self, customer_id: int) -> List[Job]:
        """Get customer's unpaid orders"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return []

            return customer.get_unpaid_jobs()
        except Exception as e:
            self.logger.error(f"Failed to get customer unpaid jobs (ID: {customer_id}): {e}")
            return []

    def get_customer_statistics(self, customer_id: int) -> Dict[str, Any]:
        """
        Get customer statistics

        Args:
            customer_id: Customer ID

        Returns:
            Customer statistics dictionary
        """
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return {}

            all_jobs = customer.get_jobs()
            unpaid_jobs = customer.get_unpaid_jobs()
            total_unpaid = customer.get_total_unpaid_amount()

            return {
                'customer_info': customer.to_dict(),
                'total_jobs': len(all_jobs),
                'completed_jobs': len([j for j in all_jobs if j.completed]),
                'unpaid_jobs': len(unpaid_jobs),
                'total_unpaid_amount': total_unpaid,
                'recent_jobs': [j.to_dict() for j in all_jobs[:5]]
            }

        except Exception as e:
            self.logger.error(f"Failed to get customer statistics (ID: {customer_id}): {e}")
            return {}

    def schedule_job_for_customer(self, customer_id: int, job_date: date) -> Tuple[bool, List[str], Optional[int]]:
        """
        Schedule a work order for customer

        Args:
            customer_id: Customer ID
            job_date: Job date

        Returns:
            (success, error_messages, job_id)
        """
        try:
            # Verify customer exists
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["Customer does not exist"], None

            # Validate date
            if job_date < date.today():
                return False, ["Job date cannot be earlier than today"], None

            # Create job
            job = Job(
                job_date=job_date,
                customer=customer_id,
                total_cost=0.0,
                completed=False,
                paid=False
            )
            job.save()

            self.logger.info(f"Scheduled job for customer {customer.full_name}")
            return True, [], job.job_id

        except Exception as e:
            self.logger.error(f"Failed to schedule job: {e}")
            db.session.rollback()
            return False, ["System error, please try again"], None
