"""
User model for authentication and authorization
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base import BaseModel
from app.utils.database import execute_query, execute_update, DatabaseError


class User(BaseModel):
    """User model for authentication"""

    _table_name = 'user'
    _primary_key = 'user_id'
    _fields = [
        'user_id', 'username', 'email', 'password_hash',
        'role', 'is_active', 'created_at', 'updated_at', 'last_login'
    ]

    # Valid roles
    ROLE_TECHNICIAN = 'technician'
    ROLE_ADMINISTRATOR = 'administrator'
    VALID_ROLES = [ROLE_TECHNICIAN, ROLE_ADMINISTRATOR]

    def __init__(self, **kwargs):
        """Initialize user instance"""
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role == self.ROLE_ADMINISTRATOR

    @property
    def is_technician(self) -> bool:
        """Check if user is a technician"""
        return self.role == self.ROLE_TECHNICIAN

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str) -> None:
        """
        Set a new password (hashed)

        Args:
            password: Plain text password to hash and store
        """
        self.password_hash = generate_password_hash(password)

    @classmethod
    def find_by_username(cls, username: str) -> Optional['User']:
        """
        Find user by username

        Args:
            username: The username to search for

        Returns:
            User instance if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE username = %s"
            result = execute_query(query, (username,), fetch_one=True)
            return cls(**result) if result else None
        except Exception as e:
            logging.error(f"Failed to find user by username: {e}")
            raise DatabaseError(f"Failed to find user: {e}")

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """
        Find user by email

        Args:
            email: The email to search for

        Returns:
            User instance if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE email = %s"
            result = execute_query(query, (email,), fetch_one=True)
            return cls(**result) if result else None
        except Exception as e:
            logging.error(f"Failed to find user by email: {e}")
            raise DatabaseError(f"Failed to find user: {e}")

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        """
        Authenticate user with username and password

        Args:
            username: The username
            password: The plain text password

        Returns:
            User instance if authentication successful, None otherwise
        """
        try:
            user = cls.find_by_username(username)
            if user and user.is_active and user.check_password(password):
                # Update last login time
                user.update_last_login()
                return user
            return None
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None

    def update_last_login(self) -> bool:
        """Update the last login timestamp"""
        try:
            query = f"UPDATE {self._table_name} SET last_login = %s WHERE {self._primary_key} = %s"
            execute_update(query, (datetime.now(), self.user_id))
            self.last_login = datetime.now()
            return True
        except Exception as e:
            logging.error(f"Failed to update last login: {e}")
            return False

    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = ROLE_TECHNICIAN
    ) -> Optional['User']:
        """
        Create a new user

        Args:
            username: The username (must be unique)
            password: The plain text password (will be hashed)
            email: Optional email address
            role: User role (technician or administrator)

        Returns:
            Created User instance, or None if creation failed
        """
        try:
            # Validate role
            if role not in cls.VALID_ROLES:
                raise ValueError(f"Invalid role: {role}")

            # Check if username exists
            if cls.find_by_username(username):
                raise ValueError("Username already exists")

            # Check if email exists
            if email and cls.find_by_email(email):
                raise ValueError("Email already registered")

            # Hash password
            password_hash = generate_password_hash(password)

            # Insert user
            query = f"""
                INSERT INTO {cls._table_name}
                (username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """
            user_id = execute_update(query, (username, email, password_hash, role))

            if user_id:
                return cls.find_by_id(user_id)
            return None

        except Exception as e:
            logging.error(f"Failed to create user: {e}")
            raise DatabaseError(f"Failed to create user: {e}")

    def update_password(self, new_password: str) -> bool:
        """
        Update user's password

        Args:
            new_password: The new plain text password

        Returns:
            True if successful, False otherwise
        """
        try:
            new_hash = generate_password_hash(new_password)
            query = f"""
                UPDATE {self._table_name}
                SET password_hash = %s, updated_at = %s
                WHERE {self._primary_key} = %s
            """
            execute_update(query, (new_hash, datetime.now(), self.user_id))
            self.password_hash = new_hash
            return True
        except Exception as e:
            logging.error(f"Failed to update password: {e}")
            return False

    def deactivate(self) -> bool:
        """Deactivate user account"""
        try:
            query = f"""
                UPDATE {self._table_name}
                SET is_active = 0, updated_at = %s
                WHERE {self._primary_key} = %s
            """
            execute_update(query, (datetime.now(), self.user_id))
            self.is_active = False
            return True
        except Exception as e:
            logging.error(f"Failed to deactivate user: {e}")
            return False

    def activate(self) -> bool:
        """Activate user account"""
        try:
            query = f"""
                UPDATE {self._table_name}
                SET is_active = 1, updated_at = %s
                WHERE {self._primary_key} = %s
            """
            execute_update(query, (datetime.now(), self.user_id))
            self.is_active = True
            return True
        except Exception as e:
            logging.error(f"Failed to activate user: {e}")
            return False

    @classmethod
    def get_by_role(cls, role: str) -> List['User']:
        """
        Get all users with a specific role

        Args:
            role: The role to filter by

        Returns:
            List of User instances
        """
        return cls.find_by_condition({'role': role, 'is_active': True})

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary

        Args:
            include_sensitive: Whether to include sensitive fields

        Returns:
            Dictionary representation of user
        """
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else None,
            'last_login': str(self.last_login) if self.last_login else None
        }

        if include_sensitive:
            data['updated_at'] = str(self.updated_at) if self.updated_at else None

        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
