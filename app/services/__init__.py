"""
Services Package
Business logic layer for the Automotive Repair Management System
"""
from app.services.customer_service import CustomerService
from app.services.job_service import JobService
from app.services.billing_service import BillingService
from app.services.auth_service import AuthService, NeonAuthService, neon_auth

__all__ = [
    'CustomerService',
    'JobService',
    'BillingService',
    'AuthService',
    'NeonAuthService',
    'neon_auth'
]
