"""
Authentication Service
Handles Neon Auth JWT authentication (Better Auth)
All authentication flows go through Neon Auth - no local password auth
"""
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
import logging
import jwt
import requests
from functools import wraps
from flask import request, current_app, g, session, url_for
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
        auth_url = auth_url.rstrip('/')
        return f"{auth_url}/.well-known/jwks.json"

    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Neon Auth (cached for 1 hour)"""
        now = datetime.utcnow()

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
                return self._jwks
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a Neon Auth JWT token"""
        try:
            jwks = self.get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            alg = unverified_header.get('alg', 'RS256')

            rsa_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break

            if not rsa_key:
                logger.warning(f"No matching key found in JWKS for kid: {kid}")
                if jwks.get('keys'):
                    rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwks['keys'][0])
                else:
                    return None

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
        """Get or create user from Neon Auth token"""
        payload = self.verify_token(token)
        if not payload:
            # JWT verification failed — try opaque session token validation
            payload = self.validate_session_token(token)
            if not payload:
                return None
        return User.authenticate_with_jwt(payload)

    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an opaque session token by calling Neon Auth's get-session API.
        Used as fallback when JWT verification fails (Better Auth may issue opaque tokens).
        """
        try:
            auth_url = self.auth_url
            if not auth_url:
                return None

            auth_url = auth_url.rstrip('/')
            response = requests.get(
                f"{auth_url}/get-session",
                headers={
                    'Cookie': f'better-auth.session_token={token}'
                },
                timeout=10
            )

            if not response.ok:
                return None

            data = response.json()
            session_data = data.get('session')
            user_data = data.get('user')

            if not user_data:
                return None

            # Return a payload compatible with authenticate_with_jwt
            return {
                'sub': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'email_verified': user_data.get('emailVerified', False),
            }
        except Exception as e:
            logger.warning(f"Session token validation failed: {e}")
            return None

    def get_neon_auth_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user details from Neon Auth neon_auth schema"""
        try:
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
    """Authentication service - all auth flows via Neon Auth"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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

    def authenticate_jwt(self, token: str) -> Optional[User]:
        """Authenticate with Neon Auth JWT"""
        try:
            return neon_auth.get_user_from_token(token)
        except Exception as e:
            self.logger.error(f"JWT authentication error: {e}")
            return None

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user from request context"""
        if hasattr(g, 'current_user') and g.current_user is not None:
            return g.current_user

        # Try JWT authentication (Authorization header)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            user = self.authenticate_jwt(token)
            if user:
                g.current_user = user
                return user

        # Check for token in cookie (Neon Auth web flow)
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

    def establish_session(self, user: User) -> None:
        """Establish Flask session for an authenticated user (no tenant context yet)"""
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['logged_in'] = True
        session['auth_method'] = 'neon_auth'
        user.update_last_login()

    def establish_tenant_session(self, user_id: int, tenant_id: int) -> bool:
        """Set tenant context in session from TenantMembership"""
        try:
            from app.models.tenant import Tenant
            membership = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                )
            ).scalar_one_or_none()

            if not membership:
                return False

            tenant = Tenant.find_by_id(tenant_id)
            if not tenant:
                return False

            session['current_tenant_id'] = tenant_id
            session['current_tenant_slug'] = tenant.slug
            session['current_tenant_name'] = tenant.name
            session['current_role'] = membership.role
            return True

        except Exception as e:
            self.logger.error(f"Failed to establish tenant session: {e}")
            return False

    def resolve_post_auth_redirect(self, user_id: int) -> str:
        """Determine where to redirect after authentication based on memberships"""
        memberships = self._get_user_memberships(user_id)

        if not memberships:
            return url_for('auth.no_organization')

        if len(memberships) == 1:
            # Auto-select the single tenant
            self.establish_tenant_session(user_id, memberships[0]['tenant_id'])
            return url_for('main.dashboard')

        # Multiple memberships - try default first
        default = next((m for m in memberships if m['is_default']), None)
        if default:
            self.establish_tenant_session(user_id, default['tenant_id'])
            return url_for('main.dashboard')

        return url_for('auth.select_tenant')

    def switch_tenant(self, user_id: int, tenant_id: int) -> Tuple[bool, Optional[str]]:
        """Switch the active tenant for the current session."""
        success = self.establish_tenant_session(user_id, tenant_id)
        if success:
            return True, None
        return False, "You do not have access to this organization"

    def logout_user(self) -> None:
        """Clear user from session"""
        session.clear()
        if hasattr(g, 'current_user'):
            g.current_user = None
