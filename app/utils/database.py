"""
Database Utilities
SQLAlchemy database initialization and helper functions
"""
import logging
from flask import Flask
from app.extensions import db

logger = logging.getLogger(__name__)


def init_database(app: Flask) -> None:
    """
    Initialize SQLAlchemy database with the Flask app

    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Create tables if they don't exist (for development)
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from app.models import Customer, Job, JobService, JobPart, Service, Part, User

        # Only create tables in development/testing
        if app.config.get('ENV') != 'production':
            db.create_all()
            logger.info("Database tables created/verified")

    logger.info("Database initialized successfully")


class DatabaseError(Exception):
    """Custom database exception"""
    pass


class ValidationError(Exception):
    """Data validation exception"""
    pass


# Legacy compatibility functions - these delegate to SQLAlchemy
def execute_query(query: str, params=None, fetch_one: bool = False):
    """
    Legacy function for raw SQL queries
    Use SQLAlchemy ORM methods instead when possible
    """
    from sqlalchemy import text

    result = db.session.execute(text(query), params or {})

    if query.strip().upper().startswith('SELECT'):
        if fetch_one:
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows] if rows else []
    return None


def execute_update(query: str, params=None) -> int:
    """
    Legacy function for raw SQL updates
    Use SQLAlchemy ORM methods instead when possible
    """
    from sqlalchemy import text

    result = db.session.execute(text(query), params or {})
    db.session.commit()
    return result.rowcount
