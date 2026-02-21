"""
Authentication Service
Handles Neon Auth JWT authentication (Better Auth)
All authentication flows go through Neon Auth - no local password auth
"""
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
import logging
import hashlib
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
        Tries multiple header strategies since Better Auth accepts tokens in different ways.
        """
        auth_url = self.auth_url
        if not auth_url:
            return None

        auth_url = auth_url.rstrip('/')
        get_session_url = f"{auth_url}/get-session"

        # Strategy 1: Pass token as cookie
        try:
            response = requests.get(
                get_session_url,
                headers={
                    'Cookie': f'better-auth.session_token={token}'
                },
                timeout=10
            )
            body_text = response.text[:500] if response.text else '(empty)'
            logger.info(f"validate_session: cookie strategy status={response.status_code} body={body_text}")
            result = self._parse_session_response(response)
            if result:
                logger.info(f"validate_session: cookie strategy SUCCESS sub={result.get('sub')}")
                return result
        except Exception as e:
            logger.warning(f"Session validation via cookie failed: {e}")

        # Strategy 2: Pass token as Bearer authorization
        try:
            response = requests.get(
                get_session_url,
                headers={
                    'Authorization': f'Bearer {token}'
                },
                timeout=10
            )
            body_text = response.text[:500] if response.text else '(empty)'
            logger.info(f"validate_session: bearer strategy status={response.status_code} body={body_text}")
            result = self._parse_session_response(response)
            if result:
                logger.info(f"validate_session: bearer strategy SUCCESS sub={result.get('sub')}")
                return result
        except Exception as e:
            logger.warning(f"Session validation via Bearer failed: {e}")

        # Strategy 3: Look up session in neon_auth DB (plain token)
        try:
            result = self._lookup_session_in_db(token)
            if result:
                logger.info(f"validate_session: DB plain lookup SUCCESS sub={result.get('sub')}")
                return result
            else:
                logger.info("validate_session: DB plain lookup returned no result")
        except Exception as e:
            logger.warning(f"Session DB plain lookup failed: {e}")

        # Strategy 4: Look up session in neon_auth DB (SHA-256 hashed token)
        # Better Auth stores hashed session tokens in the database
        try:
            hashed = hashlib.sha256(token.encode('utf-8')).hexdigest()
            logger.info(f"validate_session: trying hashed token lookup hash_prefix={hashed[:16]}...")
            result = self._lookup_session_in_db(hashed)
            if result:
                logger.info(f"validate_session: DB hashed lookup SUCCESS sub={result.get('sub')}")
                return result
            else:
                logger.info("validate_session: DB hashed lookup returned no result")
        except Exception as e:
            logger.warning(f"Session DB hashed lookup failed: {e}")

        logger.warning(f"All session token validation strategies failed for token prefix={token[:20]}...")
        return None

    def _parse_session_response(self, response) -> Optional[Dict[str, Any]]:
        """Parse a get-session response into a JWT-compatible payload"""
        if not response.ok:
            return None

        try:
            data = response.json()
        except Exception:
            return None

        user_data = data.get('user')
        if not user_data:
            return None

        return {
            'sub': user_data.get('id'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'email_verified': user_data.get('emailVerified', user_data.get('email_verified', False)),
        }

    def _lookup_session_in_db(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Look up a session token directly in the neon_auth schema.
        Tries multiple column name conventions (camelCase and snake_case).
        """
        # Try camelCase columns first (Better Auth default with Drizzle)
        for query_sql in [
            # camelCase columns (Drizzle ORM default)
            """
                SELECT u.id, u.email, u.name, u."emailVerified" as email_verified
                FROM neon_auth.session s
                JOIN neon_auth."user" u ON s."userId" = u.id
                WHERE s.token = :token
                  AND s."expiresAt" > NOW()
            """,
            # snake_case columns (Prisma / some configurations)
            """
                SELECT u.id, u.email, u.name, u.email_verified
                FROM neon_auth.session s
                JOIN neon_auth."user" u ON s.user_id = u.id
                WHERE s.token = :token
                  AND s.expires_at > NOW()
            """,
            # all lowercase (PostgreSQL default unquoted)
            """
                SELECT u.id, u.email, u.name, u.emailverified as email_verified
                FROM neon_auth.session s
                JOIN neon_auth."user" u ON s.userid = u.id
                WHERE s.token = :token
                  AND s.expiresat > NOW()
            """,
        ]:
            try:
                result = db.session.execute(
                    db.text(query_sql),
                    {'token': token}
                ).fetchone()

                if result:
                    return {
                        'sub': result.id,
                        'email': result.email,
                        'name': result.name,
                        'email_verified': getattr(result, 'email_verified', False),
                    }
            except Exception as e:
                logger.info(f"neon_auth DB lookup variant failed: {e}")
                # Rollback the failed query to keep the session usable
                try:
                    db.session.rollback()
                except Exception:
                    pass
                continue

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
