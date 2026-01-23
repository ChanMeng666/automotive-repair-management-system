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

__all__ = [
    'db',
    'Customer',
    'Job',
    'JobService',
    'JobPart',
    'Service',
    'Part',
    'User'
]
