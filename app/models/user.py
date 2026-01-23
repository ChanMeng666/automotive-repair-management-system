"""
User Model - SQLAlchemy ORM
Authentication and authorization with Stack Auth JWT support
"""
from typing import Optional, List
from datetime import datetime
import logging
from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin


class User(db.Model, BaseModelMixin, TimestampMixin):
    """User model for authentication"""

    __tablename__ = 'user'

    # Role constants
    ROLE_TECHNICIAN = 'technician'
    ROLE_ADMINISTRATOR = 'administrator'
    VALID_ROLES = [ROLE_TECHNICIAN, ROLE_ADMINISTRATOR]

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=ROLE_TECHNICIAN, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Stack Auth integration fields
    stack_auth_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)

    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role == self.ROLE_ADMINISTRATOR

    @property
    def is_technician(self) -> bool:
        """Check if user is a technician"""
        return self.role == self.ROLE_TECHNICIAN

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str) -> None:
        """Set a new password (hashed)"""
        self.password_hash = generate_password_hash(password)

    @classmethod
    def find_by_username(cls, username: str) -> Optional['User']:
        """Find user by username"""
        query = db.select(cls).where(cls.username == username)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email"""
        query = db.select(cls).where(cls.email == email)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def find_by_stack_auth_id(cls, stack_auth_user_id: str) -> Optional['User']:
        """Find user by Stack Auth user ID"""
        query = db.select(cls).where(cls.stack_auth_user_id == stack_auth_user_id)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password"""
        user = cls.find_by_username(username)
        if user and user.is_active and user.check_password(password):
            user.update_last_login()
            return user
        return None

    @classmethod
    def authenticate_with_jwt(cls, jwt_payload: dict) -> Optional['User']:
        """
        Authenticate user with Stack Auth JWT payload

        Args:
            jwt_payload: Decoded JWT payload from Stack Auth

        Returns:
            User instance if found/created, None otherwise
        """
        stack_auth_user_id = jwt_payload.get('sub')
        if not stack_auth_user_id:
            return None

        # Try to find existing user
        user = cls.find_by_stack_auth_id(stack_auth_user_id)
        if user:
            if user.is_active:
                user.update_last_login()
                return user
            return None

        # Create new user from JWT if not found
        email = jwt_payload.get('email')
        if email:
            # Check if email already exists
            existing = cls.find_by_email(email)
            if existing:
                # Link existing user to Stack Auth
                existing.stack_auth_user_id = stack_auth_user_id
                existing.update_last_login()
                db.session.commit()
                return existing

        # Create new user
        username = email.split('@')[0] if email else f"user_{stack_auth_user_id[:8]}"
        # Ensure unique username
        base_username = username
        counter = 1
        while cls.find_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        user = cls(
            username=username,
            email=email,
            password_hash=generate_password_hash(__import__('secrets').token_urlsafe(32)),
            role=cls.ROLE_TECHNICIAN,
            stack_auth_user_id=stack_auth_user_id,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        user.update_last_login()
        return user

    def update_last_login(self) -> bool:
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
        return True

    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = ROLE_TECHNICIAN
    ) -> Optional['User']:
        """Create a new user"""
        # Validate role
        if role not in cls.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")

        # Check if username exists
        if cls.find_by_username(username):
            raise ValueError("Username already exists")

        # Check if email exists
        if email and cls.find_by_email(email):
            raise ValueError("Email already registered")

        # Create user
        user = cls(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            role=role,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user

    def update_password(self, new_password: str) -> bool:
        """Update user's password"""
        self.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True

    def deactivate(self) -> bool:
        """Deactivate user account"""
        self.is_active = False
        db.session.commit()
        return True

    def activate(self) -> bool:
        """Activate user account"""
        self.is_active = True
        db.session.commit()
        return True

    @classmethod
    def get_by_role(cls, role: str) -> List['User']:
        """Get all users with a specific role"""
        query = db.select(cls).where(db.and_(cls.role == role, cls.is_active == True))
        return list(db.session.execute(query).scalars())

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive:
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
            data['stack_auth_user_id'] = self.stack_auth_user_id

        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
