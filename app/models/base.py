"""
Base Model Mixins
Provides common functionality for SQLAlchemy models
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Type, TypeVar
from sqlalchemy import inspect
from app.extensions import db

T = TypeVar('T', bound='BaseModelMixin')


class BaseModelMixin:
    """Mixin providing common model functionality"""

    def save(self) -> 'BaseModelMixin':
        """Save the model instance to database"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> bool:
        """Delete the model instance from database"""
        db.session.delete(self)
        db.session.commit()
        return True

    @classmethod
    def find_by_id(cls: Type[T], pk_value: Any) -> Optional[T]:
        """Find a record by primary key"""
        return db.session.get(cls, pk_value)

    @classmethod
    def find_all(cls: Type[T], order_by: Optional[str] = None) -> List[T]:
        """Find all records, optionally ordered"""
        query = db.select(cls)
        if order_by:
            # Parse order_by string to column references
            order_parts = [part.strip() for part in order_by.split(',')]
            for part in order_parts:
                if ' DESC' in part.upper():
                    col_name = part.upper().replace(' DESC', '').strip().lower()
                    if hasattr(cls, col_name):
                        query = query.order_by(getattr(cls, col_name).desc())
                else:
                    col_name = part.upper().replace(' ASC', '').strip().lower()
                    if hasattr(cls, col_name):
                        query = query.order_by(getattr(cls, col_name))
        return list(db.session.execute(query).scalars())

    @classmethod
    def count(cls: Type[T], **filters) -> int:
        """Count records matching filters"""
        query = db.select(db.func.count()).select_from(cls)
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)
        result = db.session.execute(query).scalar()
        return result or 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.key)
            # Handle datetime objects
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.key] = value
        return result

    def update(self, **kwargs) -> 'BaseModelMixin':
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def __repr__(self) -> str:
        """String representation"""
        mapper = inspect(self.__class__)
        pk_cols = [col.key for col in mapper.primary_key]
        pk_values = [getattr(self, col) for col in pk_cols]
        pk_str = ', '.join(f"{k}={v}" for k, v in zip(pk_cols, pk_values))
        return f"<{self.__class__.__name__}({pk_str})>"


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
