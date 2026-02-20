"""
Tenant Context Middleware
Sets g.current_tenant_id from URL path slug, session, or header.
"""
import logging
from flask import g, request, session, abort
from app.extensions import db

logger = logging.getLogger(__name__)

# Routes that don't require tenant context
TENANT_EXEMPT_PREFIXES = (
    '/auth/',
    '/static/',
    '/login',
    '/logout',
    '/register',
    '/favicon',
    '/about',
    '/help',
    '/billing/webhook',
)

TENANT_EXEMPT_ENDPOINTS = {
    'main.index',
    'main.login',
    'main.login_post',
    'main.logout',
    'main.about',
    'main.help_page',
    'static',
}


def init_tenant_middleware(app):
    """Register tenant middleware with Flask app"""

    @app.before_request
    def set_tenant_context():
        """Set g.current_tenant_id before each request"""
        g.current_tenant_id = None
        g.current_tenant = None
        g.current_membership = None

        # Skip for exempt routes
        path = request.path
        for prefix in TENANT_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return None

        endpoint = request.endpoint
        if endpoint in TENANT_EXEMPT_ENDPOINTS:
            return None

        # Strategy 1: Extract tenant from URL path /org/<slug>/...
        if path.startswith('/org/'):
            parts = path.split('/')
            if len(parts) >= 3:
                slug = parts[2]
                tenant = _resolve_tenant_by_slug(slug)
                if tenant:
                    g.current_tenant_id = tenant.tenant_id
                    g.current_tenant = tenant
                    _load_membership()
                    return None
                else:
                    abort(404)

        # Strategy 2: Session-based tenant
        tenant_id = session.get('current_tenant_id')
        if tenant_id:
            tenant = _resolve_tenant_by_id(tenant_id)
            if tenant:
                g.current_tenant_id = tenant.tenant_id
                g.current_tenant = tenant
                _load_membership()
                return None

        # Strategy 3: X-Tenant-ID header (API)
        header_tenant_id = request.headers.get('X-Tenant-ID')
        if header_tenant_id:
            try:
                tenant_id = int(header_tenant_id)
                tenant = _resolve_tenant_by_id(tenant_id)
                if tenant:
                    g.current_tenant_id = tenant.tenant_id
                    g.current_tenant = tenant
                    _load_membership()
                    return None
            except (ValueError, TypeError):
                pass

        # No tenant context - this is OK for some routes
        return None

    @app.context_processor
    def inject_tenant_context():
        """Make tenant context available in all templates"""
        user_tenants = None
        user_id = session.get('user_id')
        if user_id and session.get('logged_in'):
            try:
                from app.services.tenant_service import TenantService
                tenant_service = TenantService()
                user_tenants = tenant_service.get_user_tenants(user_id)
            except Exception:
                user_tenants = None

        return {
            'current_tenant': getattr(g, 'current_tenant', None),
            'current_tenant_id': getattr(g, 'current_tenant_id', None),
            'current_membership': getattr(g, 'current_membership', None),
            'user_tenants': user_tenants,
        }


def _resolve_tenant_by_slug(slug):
    """Look up tenant by slug"""
    from app.models.tenant import Tenant
    return Tenant.find_by_slug(slug)


def _resolve_tenant_by_id(tenant_id):
    """Look up tenant by ID"""
    from app.models.tenant import Tenant
    return Tenant.find_by_id(tenant_id)


def _load_membership():
    """Load current user's membership in current tenant"""
    user_id = session.get('user_id')
    tenant_id = getattr(g, 'current_tenant_id', None)
    if not user_id or not tenant_id:
        return

    from app.models.tenant_membership import TenantMembership
    membership = db.session.execute(
        db.select(TenantMembership).where(
            db.and_(
                TenantMembership.user_id == user_id,
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.status == 'active'
            )
        )
    ).scalar_one_or_none()
    g.current_membership = membership
