"""
Authentication Service
Handles both traditional and Stack Auth JWT authentication
"""
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
import logging
import jwt
import requests
from functools import wraps
from flask import request, current_app, g, session
from app.models.user import User
from app.extensions import db

logger = logging.getLogger(__name__)


class StackAuthService:
    """Stack Auth integration service for JWT authentication"""

    def __init__(self, app=None):
        self.app = app
        self._jwks = None
        self._jwks_fetched_at = None

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

    @property
    def project_id(self) -> Optional[str]:
        """Get Stack Auth project ID from config"""
        return current_app.config.get('STACK_AUTH_PROJECT_ID')

    @property
    def jwks_url(self) -> str:
        """Get JWKS URL for Stack Auth"""
        project_id = self.project_id
        if not project_id:
            raise ValueError("STACK_AUTH_PROJECT_ID not configured")
        return f"https://api.stack-auth.com/api/v1/projects/{project_id}/.well-known/jwks.json"

    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Stack Auth (cached for 1 hour)"""
        now = datetime.utcnow()

        # Return cached JWKS if still valid
        if self._jwks and self._jwks_fetched_at:
            if (now - self._jwks_fetched_at) < timedelta(hours=1):
                return self._jwks

        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            self._jwks = response.json()
            self._jwks_fetched_at = now
            return self._jwks
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks:
                return self._jwks  # Return stale cache on error
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Stack Auth JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Get JWKS
            jwks = self.get_jwks()

            # Get token header to find key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            # Find matching key
            rsa_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break

            if not rsa_key:
                logger.warning("No matching key found in JWKS")
                return None

            # Verify token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=self.project_id,
                options={'verify_exp': True}
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get or create user from Stack Auth token

        Args:
            token: JWT token string

        Returns:
            User instance or None
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        return User.authenticate_with_jwt(payload)


# Global instance
stack_auth = StackAuthService()


class AuthService:
    """Combined authentication service supporting both password and JWT auth"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def authenticate_password(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate with username and password

        Args:
            username: Username
            password: Plain text password

        Returns:
            User if authenticated, None otherwise
        """
        return User.authenticate(username, password)

    def authenticate_jwt(self, token: str) -> Optional[User]:
        """
        Authenticate with Stack Auth JWT

        Args:
            token: JWT token

        Returns:
            User if authenticated, None otherwise
        """
        try:
            return stack_auth.get_user_from_token(token)
        except Exception as e:
            self.logger.error(f"JWT authentication error: {e}")
            return None

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user from request context"""
        # Check if already loaded
        if hasattr(g, 'current_user'):
            return g.current_user

        # Try JWT authentication first (Authorization header)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            user = self.authenticate_jwt(token)
            if user:
                g.current_user = user
                return user

        # Fall back to session-based authentication
        user_id = session.get('user_id')
        if user_id:
            user = User.find_by_id(user_id)
            if user and user.is_active:
                g.current_user = user
                return user

        g.current_user = None
        return None

    def login_user(self, user: User) -> None:
        """Store user in session"""
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.role
        user.update_last_login()

    def logout_user(self) -> None:
        """Clear user from session"""
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('role', None)
        if hasattr(g, 'current_user'):
            g.current_user = None

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = User.ROLE_TECHNICIAN
    ) -> Tuple[bool, List[str], Optional[User]]:
        """
        Create a new user

        Returns:
            (success, errors, user)
        """
        try:
            user = User.create(username, password, email, role)
            return True, [], user
        except ValueError as e:
            return False, [str(e)], None
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            db.session.rollback()
            return False, ["System error"], None


# Decorator for requiring authentication
def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        user = auth_service.get_current_user()
        if not user:
            # For API requests, return 401
            if request.is_json or request.headers.get('Authorization'):
                return {'error': 'Authentication required'}, 401
            # For web requests, redirect to login
            from flask import redirect, url_for, flash
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require administrator role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        user = auth_service.get_current_user()
        if not user:
            if request.is_json or request.headers.get('Authorization'):
                return {'error': 'Authentication required'}, 401
            from flask import redirect, url_for, flash
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        if not user.is_admin:
            if request.is_json or request.headers.get('Authorization'):
                return {'error': 'Administrator access required'}, 403
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def technician_required(f):
    """Decorator to require technician or administrator role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        user = auth_service.get_current_user()
        if not user:
            if request.is_json or request.headers.get('Authorization'):
                return {'error': 'Authentication required'}, 401
            from flask import redirect, url_for, flash
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        if not (user.is_technician or user.is_admin):
            if request.is_json or request.headers.get('Authorization'):
                return {'error': 'Technician access required'}, 403
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
