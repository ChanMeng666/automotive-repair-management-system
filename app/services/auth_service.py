"""
Authentication Service
Handles both traditional password auth and Neon Auth JWT authentication
Neon Auth is powered by Better Auth and stores users in the neon_auth schema
"""
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
import logging
import jwt
import requests
from functools import wraps
from flask import request, current_app, g, session
from app.models.user import User
from app.models.tenant_membership import TenantMembership
from app.extensions import db

logger = logging.getLogger(__name__)


class NeonAuthService:
    """Neon Auth integration service for JWT authentication"""

    def __init__(self, app=None):
        self.app = app
        self._jwks = None
        self._jwks_fetched_at = None

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

    @property
    def auth_url(self) -> Optional[str]:
        """Get Neon Auth URL from config"""
        return current_app.config.get('NEON_AUTH_URL')

    @property
    def jwks_url(self) -> str:
        """Get JWKS URL for Neon Auth"""
        auth_url = self.auth_url
        if not auth_url:
            raise ValueError("NEON_AUTH_URL not configured")
        # Ensure no trailing slash
        auth_url = auth_url.rstrip('/')
        return f"{auth_url}/.well-known/jwks.json"

    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Neon Auth (cached for 1 hour)"""
        now = datetime.utcnow()

        # Return cached JWKS if still valid
        if self._jwks and self._jwks_fetched_at:
            if (now - self._jwks_fetched_at) < timedelta(hours=1):
                return self._jwks

        try:
            jwks_url = current_app.config.get('NEON_AUTH_JWKS_URL') or self.jwks_url
            logger.info(f"Fetching JWKS from: {jwks_url}")
            response = requests.get(jwks_url, timeout=10)
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
        Verify a Neon Auth JWT token

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
            alg = unverified_header.get('alg', 'RS256')

            # Find matching key
            rsa_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break

            if not rsa_key:
                logger.warning(f"No matching key found in JWKS for kid: {kid}")
                # Try with first available key if no kid match
                if jwks.get('keys'):
                    rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwks['keys'][0])
                else:
                    return None

            # Verify token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[alg],
                options={'verify_exp': True, 'verify_aud': False}
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
        Get or create user from Neon Auth token

        Args:
            token: JWT token string

        Returns:
            User instance or None
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        return User.authenticate_with_jwt(payload)

    def get_neon_auth_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user details from Neon Auth neon_auth schema

        Args:
            user_id: The user ID from the JWT

        Returns:
            User data dict or None
        """
        try:
            # Query the neon_auth.user table
            result = db.session.execute(
                db.text("""
                    SELECT id, email, name, email_verified, image, created_at, updated_at
                    FROM neon_auth.user
                    WHERE id = :user_id
                """),
                {'user_id': user_id}
            ).fetchone()

            if result:
                return {
                    'id': result.id,
                    'email': result.email,
                    'name': result.name,
                    'email_verified': result.email_verified,
                    'image': result.image,
                    'created_at': result.created_at,
                    'updated_at': result.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"Failed to fetch Neon Auth user: {e}")
            return None


# Global instance
neon_auth = NeonAuthService()


class AuthService:
    """Combined authentication service supporting both password and JWT auth"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def authenticate(self, username: str, password: str, user_type: str = 'technician') -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Authenticate with username and password (main login method).
        Returns user data including tenant memberships.

        Args:
            username: Username
            password: Plain text password
            user_type: Expected role ('technician' or 'administrator')

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            user = User.authenticate(username, password)

            if user:
                # Check if user role matches expected type (or allow admin to log in as any role)
                if user.role != user_type and not user.is_admin:
                    return False, {}, f"Your account is not registered as a {user_type}"

                # Fetch tenant memberships
                memberships = self._get_user_memberships(user.user_id)

                user_data = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'role': user.role,
                    'email': user.email,
                    'memberships': memberships,
                }
                return True, user_data, None
            else:
                return False, {}, "Invalid username or password"

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, {}, "Authentication failed. Please try again."

    def _get_user_memberships(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active tenant memberships for a user"""
        try:
            rows = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                )
            ).scalars().all()

            return [
                {
                    'tenant_id': m.tenant_id,
                    'role': m.role,
                    'is_default': m.is_default,
                }
                for m in rows
            ]
        except Exception as e:
            self.logger.error(f"Failed to get memberships: {e}")
            return []

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
        Authenticate with Neon Auth JWT

        Args:
            token: JWT token

        Returns:
            User if authenticated, None otherwise
        """
        try:
            return neon_auth.get_user_from_token(token)
        except Exception as e:
            self.logger.error(f"JWT authentication error: {e}")
            return None

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user from request context"""
        # Check if already loaded
        if hasattr(g, 'current_user') and g.current_user is not None:
            return g.current_user

        # Try JWT authentication first (Authorization header)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            user = self.authenticate_jwt(token)
            if user:
                g.current_user = user
                return user

        # Check for token in cookie (for Neon Auth web flow)
        token = request.cookies.get('better-auth.session_token')
        if token:
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
        """Store user in session. Auto-selects tenant if user has exactly one."""
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.role
        user.update_last_login()

        # Auto-select tenant
        memberships = self._get_user_memberships(user.user_id)
        if len(memberships) == 1:
            session['tenant_id'] = memberships[0]['tenant_id']
            session['tenant_role'] = memberships[0]['role']
        elif memberships:
            # Pick the default membership
            default = next((m for m in memberships if m['is_default']), None)
            if default:
                session['tenant_id'] = default['tenant_id']
                session['tenant_role'] = default['role']

    def switch_tenant(self, user_id: int, tenant_id: int) -> Tuple[bool, Optional[str]]:
        """
        Switch the active tenant for the current session.

        Returns:
            (success, error_message)
        """
        try:
            membership = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                )
            ).scalar_one_or_none()

            if not membership:
                return False, "You do not have access to this organization"

            session['tenant_id'] = tenant_id
            session['tenant_role'] = membership.role
            return True, None

        except Exception as e:
            self.logger.error(f"Failed to switch tenant: {e}")
            return False, "Failed to switch organization"

    def logout_user(self) -> None:
        """Clear user from session"""
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('role', None)
        session.pop('tenant_id', None)
        session.pop('tenant_role', None)
        if hasattr(g, 'current_user'):
            g.current_user = None

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = 'technician'
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
