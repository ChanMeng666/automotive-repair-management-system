"""
Flask Extensions
Centralized initialization of Flask extensions
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass


# Initialize SQLAlchemy with custom base class
db = SQLAlchemy(model_class=Base)
