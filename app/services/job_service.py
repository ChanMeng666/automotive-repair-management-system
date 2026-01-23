"""
Job Service
Business logic for work order operations using SQLAlchemy ORM
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import logging
from app.extensions import db
from app.models.job import Job
from app.models.service import Service
from app.models.part import Part


class JobService:
    """Job service class"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_current_jobs(self, page: int = 1, per_page: int = 10) -> Tuple[List[Job], int, int]:
        """
        Get current incomplete jobs with pagination

        Args:
            page: Page number
            per_page: Records per page

        Returns:
            (jobs_list, total_count, total_pages)
        """
        try:
            jobs, total = Job.get_current_jobs(page, per_page)
            total_pages = (total + per_page - 1) // per_page

            return jobs, total, total_pages

        except Exception as e:
            self.logger.error(f"Failed to get current jobs: {e}")
            raise

    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        try:
            return Job.find_by_id(job_id)
        except Exception as e:
            self.logger.error(f"Failed to get job (ID: {job_id}): {e}")
            raise

    def get_job_details(self, job_id: int) -> Dict[str, Any]:
        """
        Get detailed job information

        Args:
            job_id: Job ID

        Returns:
            Job details dictionary
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return {}

            # Get all available services and parts
            all_services = Service.get_all_sorted()
            all_parts = Part.get_all_sorted()

            return {
                'job_info': job.to_dict(),
                'services': job.get_services(),
                'parts': job.get_parts(),
                'all_services': [s.to_dict() for s in all_services],
                'all_parts': [p.to_dict() for p in all_parts],
                'job_completed': job.completed
            }

        except Exception as e:
            self.logger.error(f"Failed to get job details (ID: {job_id}): {e}")
            return {}

    def add_service_to_job(self, job_id: int, service_id: int, quantity: int) -> Tuple[bool, List[str]]:
        """
        Add service to job

        Args:
            job_id: Job ID
            service_id: Service ID
            quantity: Quantity

        Returns:
            (success, error_messages)
        """
        try:
            if quantity <= 0:
                return False, ["Quantity must be greater than 0"]

            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.completed:
                return False, ["Cannot modify a completed job"]

            service = Service.find_by_id(service_id)
            if not service:
                return False, ["Service does not exist"]

            job.add_service(service_id, quantity)
            self.logger.info(f"Added service {service.service_name} to job {job_id}")
            return True, []

        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.logger.error(f"Failed to add service: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def add_part_to_job(self, job_id: int, part_id: int, quantity: int) -> Tuple[bool, List[str]]:
        """
        Add part to job

        Args:
            job_id: Job ID
            part_id: Part ID
            quantity: Quantity

        Returns:
            (success, error_messages)
        """
        try:
            if quantity <= 0:
                return False, ["Quantity must be greater than 0"]

            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.completed:
                return False, ["Cannot modify a completed job"]

            part = Part.find_by_id(part_id)
            if not part:
                return False, ["Part does not exist"]

            job.add_part(part_id, quantity)
            self.logger.info(f"Added part {part.part_name} to job {job_id}")
            return True, []

        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.logger.error(f"Failed to add part: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def mark_job_as_completed(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        Mark job as completed

        Args:
            job_id: Job ID

        Returns:
            (success, error_messages)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.completed:
                return False, ["Job is already completed"]

            job.mark_as_completed()
            self.logger.info(f"Job {job_id} marked as completed")
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to mark job as completed: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def mark_job_as_paid(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        Mark job as paid

        Args:
            job_id: Job ID

        Returns:
            (success, error_messages)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.paid:
                return False, ["Job is already paid"]

            job.mark_as_paid()
            self.logger.info(f"Job {job_id} marked as paid")
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to mark job as paid: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]

    def get_all_jobs_with_customer_info(self) -> List[Job]:
        """Get all jobs with customer information"""
        try:
            return Job.get_all_with_customer_info()
        except Exception as e:
            self.logger.error(f"Failed to get all jobs: {e}")
            return []

    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            total_jobs = Job.count()
            completed_jobs = Job.count(completed=True)
            unpaid_jobs = Job.count(paid=False)
            overdue_jobs = Job.get_overdue_jobs()

            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'pending_jobs': total_jobs - completed_jobs,
                'unpaid_jobs': unpaid_jobs,
                'overdue_jobs': len(overdue_jobs),
                'completion_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'payment_rate': ((total_jobs - unpaid_jobs) / total_jobs * 100) if total_jobs > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get job statistics: {e}")
            return {
                'total_jobs': 0,
                'completed_jobs': 0,
                'pending_jobs': 0,
                'unpaid_jobs': 0,
                'overdue_jobs': 0,
                'completion_rate': 0,
                'payment_rate': 0
            }

    def create_job(self, customer_id: int, job_date: date) -> Tuple[bool, List[str], Optional[Job]]:
        """
        Create a new job

        Args:
            customer_id: Customer ID
            job_date: Job date

        Returns:
            (success, error_messages, job)
        """
        try:
            if job_date < date.today():
                return False, ["Job date cannot be earlier than today"], None

            job = Job(
                job_date=job_date,
                customer=customer_id,
                total_cost=0.0,
                completed=False,
                paid=False
            )
            job.save()

            self.logger.info(f"Created job for customer {customer_id}")
            return True, [], job

        except Exception as e:
            self.logger.error(f"Failed to create job: {e}")
            db.session.rollback()
            return False, ["System error, please try again"], None

    def delete_job(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        Delete job

        Args:
            job_id: Job ID

        Returns:
            (success, error_messages)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["Job does not exist"]

            if job.completed:
                return False, ["Cannot delete a completed job"]

            if job.job_services or job.job_parts:
                return False, ["Cannot delete job with services or parts"]

            job.delete()
            self.logger.info(f"Deleted job {job_id}")
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to delete job: {e}")
            db.session.rollback()
            return False, ["System error, please try again"]
