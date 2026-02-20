"""
Models Package
SQLAlchemy ORM models for the Automotive Repair Management System
"""
from app.extensions import db
from app.models.customer import Customer
from app.models.job import Job, JobService, JobPart
from app.models.service import Service
from app.models.part import Part
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.inventory import Inventory, InventoryTransaction
from app.models.subscription import Subscription

__all__ = [
    'db',
    'Customer',
    'Job',
    'JobService',
    'JobPart',
    'Service',
    'Part',
    'User',
    'Tenant',
    'TenantMembership',
    'Inventory',
    'InventoryTransaction',
    'Subscription',
]
