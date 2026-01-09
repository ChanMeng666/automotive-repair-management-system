"""
Authentication Service
Handles user authentication and session management
"""
from typing import Optional, Tuple, Dict, Any
import logging
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import db_manager


class AuthService:
    """Authentication service class"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._demo_mode = os.environ.get('AUTH_DEMO_MODE', 'false').lower() == 'true'

    def authenticate(
        self, username: str, password: str, user_type: str = 'technician'
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate a user

        Args:
            username: The username
            password: The password
            user_type: The user type (technician/administrator)

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            # First try database authentication
            user = self._authenticate_from_database(username, password)
            if user:
                self._update_last_login(user['user_id'])
                return True, user, None

            # Fall back to demo mode if enabled (for development only)
            if self._demo_mode:
                return self._authenticate_demo(username, password, user_type)

            return False, None, "Invalid username or password"

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, None, "Authentication failed. Please try again later."

    def _authenticate_from_database(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user from database

        Args:
            username: The username
            password: The password

        Returns:
            User data dict if authenticated, None otherwise
        """
        try:
            query = """
                SELECT user_id, username, email, password_hash, role, is_active
                FROM user
                WHERE username = %s AND is_active = 1
            """
            result = db_manager.execute_query(query, (username,))

            if result and len(result) > 0:
                user = result[0]
                if check_password_hash(user['password_hash'], password):
                    return {
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'email': user['email'],
                        'role': user['role']
                    }
            return None

        except Exception as e:
            # Table might not exist yet, log and return None
            self.logger.debug(f"Database auth failed (table may not exist): {e}")
            return None

    def _authenticate_demo(
        self, username: str, password: str, user_type: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Demo mode authentication (for development only)

        WARNING: This should only be enabled in development environments
        """
        # Get demo password from environment variable
        demo_password = os.environ.get('DEMO_PASSWORD')

        if not demo_password:
            self.logger.warning(
                "AUTH_DEMO_MODE is enabled but DEMO_PASSWORD is not set"
            )
            return False, None, "Demo mode not properly configured"

        if password == demo_password:
            self.logger.info(f"Demo login: {username} as {user_type}")
            return True, {
                'user_id': f'demo_{username}',
                'username': username,
                'email': f'{username}@demo.local',
                'role': user_type
            }, None

        return False, None, "Invalid username or password"

    def _update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        try:
            query = "UPDATE user SET last_login = %s WHERE user_id = %s"
            db_manager.execute_update(query, (datetime.now(), user_id))
        except Exception as e:
            self.logger.warning(f"Failed to update last login: {e}")

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str],
        role: str = 'technician'
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Create a new user

        Args:
            username: The username
            password: The password
            email: The email address (optional)
            role: The user role (technician/administrator)

        Returns:
            Tuple of (success, user_id, error_message)
        """
        try:
            # Validate role
            if role not in ('technician', 'administrator'):
                return False, None, "Invalid role"

            # Check if username already exists
            existing = db_manager.execute_query(
                "SELECT user_id FROM user WHERE username = %s",
                (username,)
            )
            if existing:
                return False, None, "Username already exists"

            # Check if email already exists
            if email:
                existing_email = db_manager.execute_query(
                    "SELECT user_id FROM user WHERE email = %s",
                    (email,)
                )
                if existing_email:
                    return False, None, "Email already registered"

            # Hash password
            password_hash = generate_password_hash(password)

            # Insert user
            query = """
                INSERT INTO user (username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """
            user_id = db_manager.execute_update(
                query, (username, email, password_hash, role)
            )

            self.logger.info(f"Created user: {username} (ID: {user_id})")
            return True, user_id, None

        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False, None, "Failed to create user"

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change a user's password

        Args:
            user_id: The user ID
            old_password: The current password
            new_password: The new password

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify old password
            user = db_manager.execute_query(
                "SELECT password_hash FROM user WHERE user_id = %s",
                (user_id,)
            )
            if not user:
                return False, "User not found"

            if not check_password_hash(user[0]['password_hash'], old_password):
                return False, "Current password is incorrect"

            # Update password
            new_hash = generate_password_hash(new_password)
            db_manager.execute_update(
                "UPDATE user SET password_hash = %s, updated_at = %s WHERE user_id = %s",
                (new_hash, datetime.now(), user_id)
            )

            self.logger.info(f"Password changed for user ID: {user_id}")
            return True, None

        except Exception as e:
            self.logger.error(f"Failed to change password: {e}")
            return False, "Failed to change password"

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = """
                SELECT user_id, username, email, role, is_active, created_at, last_login
                FROM user
                WHERE user_id = %s
            """
            result = db_manager.execute_query(query, (user_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            return None
