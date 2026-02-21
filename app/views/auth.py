"""
Authentication Routes Blueprint
Handles Neon Auth callbacks, email verification, session management, and tenant selection
"""
from flask import (
    Blueprint, request, redirect, url_for, jsonify,
    session, current_app, flash, render_template
)
import logging
import requests as http_requests
from app.services.auth_service import AuthService, neon_auth
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


# =============================================================================
# LOGIN PAGE
# =============================================================================

@auth_bp.route('/login')
def login():
    """Render the login/signup page"""
    if session.get('logged_in'):
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')


# =============================================================================
# NEON AUTH CALLBACK ROUTES
# =============================================================================

@auth_bp.route('/callback')
def callback():
    """
    OAuth callback handler for Neon Auth
    Users are redirected here after OAuth sign-in (e.g. Google via Neon Auth)
    """
    try:
        session_token = request.cookies.get('better-auth.session_token')

        if not session_token:
            session_token = request.args.get('token')

        if session_token:
            auth_service = AuthService()
            user = auth_service.authenticate_jwt(session_token)

            if user:
                auth_service.establish_session(user)
                redirect_url = auth_service.resolve_post_auth_redirect(user.user_id)
                return redirect(redirect_url)

        # No server-side token available — render bridge page that fetches
        # the session from Neon Auth client-side and forwards to Flask
        logger.info("OAuth callback without server-side token, rendering bridge page")
        return render_template('auth/oauth_completing.html')

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/neon-callback', methods=['POST'])
def neon_callback():
    """
    API endpoint for JavaScript client to notify backend of successful auth.
    Called after sign-in or sign-up + verification via neon-auth.js.
    Accepts token from request body (preferred) or falls back to cookie.
    """
    debug_info = {}
    try:
        # Try token from request body first (works cross-origin)
        session_token = None
        body = request.get_json(silent=True) or {}
        debug_info['body_keys'] = list(body.keys())
        debug_info['has_body_token'] = bool(body.get('token'))

        if body.get('token'):
            session_token = body['token']
            debug_info['token_source'] = 'body'
            debug_info['token_length'] = len(session_token)
            debug_info['token_prefix'] = session_token[:30] + '...'

        # Fall back to cookie
        if not session_token:
            session_token = request.cookies.get('better-auth.session_token')
            if session_token:
                debug_info['token_source'] = 'cookie'
                debug_info['token_length'] = len(session_token)
                debug_info['token_prefix'] = session_token[:30] + '...'

        # Log all cookies received (names only, not values)
        debug_info['cookie_names'] = list(request.cookies.keys())

        if not session_token:
            debug_info['error'] = 'no_token_found'
            logger.warning(f"neon-callback: no token. debug={debug_info}")
            return jsonify({'error': 'No session token', 'debug': debug_info}), 401

        auth_service = AuthService()

        # Try JWT verification
        jwt_payload = neon_auth.verify_token(session_token)
        debug_info['jwt_valid'] = jwt_payload is not None
        if jwt_payload:
            debug_info['jwt_sub'] = jwt_payload.get('sub')
            debug_info['jwt_email'] = jwt_payload.get('email')

        # Try opaque session validation
        if not jwt_payload:
            opaque_payload = neon_auth.validate_session_token(session_token)
            debug_info['opaque_valid'] = opaque_payload is not None
            if opaque_payload:
                debug_info['opaque_sub'] = opaque_payload.get('sub')
                debug_info['opaque_email'] = opaque_payload.get('email')

        user = auth_service.authenticate_jwt(session_token)
        debug_info['user_found'] = user is not None

        if not user:
            # Fallback: client may have passed user data from getSession()
            client_user = body.get('user')
            debug_info['has_client_user'] = client_user is not None
            if client_user and client_user.get('id') and client_user.get('email'):
                logger.info(f"neon-callback: trying client user data fallback id={client_user.get('id')}")
                # Clean up any dirty DB transaction from failed lookups
                try:
                    db.session.rollback()
                except Exception:
                    pass
                fallback_payload = {
                    'sub': client_user['id'],
                    'email': client_user['email'],
                    'name': client_user.get('name', ''),
                    'email_verified': client_user.get('emailVerified', False),
                }
                user = User.authenticate_with_jwt(fallback_payload)
                debug_info['fallback_user_found'] = user is not None

        if user:
            debug_info['user_id'] = user.user_id
            debug_info['username'] = user.username
            auth_service.establish_session(user)
            redirect_url = auth_service.resolve_post_auth_redirect(user.user_id)

            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'redirect': redirect_url,
                'debug': debug_info
            })

        logger.warning(f"neon-callback: auth failed. debug={debug_info}")
        return jsonify({'error': 'Invalid session', 'debug': debug_info}), 401

    except Exception as e:
        debug_info['exception'] = str(e)
        logger.error(f"Neon callback error: {e}, debug={debug_info}")
        return jsonify({'error': str(e), 'debug': debug_info}), 500


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Proxy email OTP verification to Neon Auth"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')

        if not email or not otp:
            return jsonify({'error': 'Email and verification code are required'}), 400

        neon_auth_url = current_app.config.get('NEON_AUTH_URL', '').rstrip('/')
        if not neon_auth_url:
            return jsonify({'error': 'Auth service not configured'}), 500

        response = http_requests.post(
            f"{neon_auth_url}/email-otp/verify-email",
            json={'email': email, 'otp': otp},
            timeout=10
        )

        if response.ok:
            return jsonify({'success': True})

        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        return jsonify({
            'error': error_data.get('message', 'Verification failed')
        }), response.status_code

    except Exception as e:
        logger.error(f"Email verification error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-email')
def verify_email_page():
    """Standalone email verification page for users who navigated away"""
    return render_template('auth/verify_email.html')


# =============================================================================
# FORGOT PASSWORD PROXY
# =============================================================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Proxy forgot-password requests to Neon Auth to avoid cross-origin issues"""
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        neon_auth_url = current_app.config.get('NEON_AUTH_URL', '').rstrip('/')
        if not neon_auth_url:
            return jsonify({'error': 'Auth service not configured'}), 500

        response = http_requests.post(
            f"{neon_auth_url}/forget-password/email",
            json={'email': email},
            timeout=10
        )

        if response.ok:
            return jsonify({'success': True})

        error_data = {}
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
        return jsonify({
            'error': error_data.get('message', 'Could not send reset email')
        }), response.status_code

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SESSION & API ROUTES
# =============================================================================

@auth_bp.route('/session')
def get_session():
    """Get current session info for the frontend"""
    if session.get('logged_in'):
        return jsonify({
            'authenticated': True,
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('current_role'),
            'tenant_id': session.get('current_tenant_id'),
            'auth_method': session.get('auth_method', 'neon_auth')
        })

    return jsonify({'authenticated': False})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """API endpoint for logout"""
    try:
        # Clear Flask session
        session.clear()

        response_data = {
            'success': True,
            'message': 'Logged out successfully'
        }

        # Include Neon Auth sign-out URL for client-side cleanup
        neon_auth_url = current_app.config.get('NEON_AUTH_URL', '')
        if neon_auth_url:
            response_data['neon_signout_url'] = f"{neon_auth_url.rstrip('/')}/sign-out"

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify a Neon Auth JWT token"""
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'valid': False, 'error': 'No token provided'}), 400

        payload = neon_auth.verify_token(token)

        if payload:
            return jsonify({
                'valid': True,
                'payload': {
                    'sub': payload.get('sub'),
                    'email': payload.get('email'),
                    'name': payload.get('name')
                }
            })

        return jsonify({'valid': False, 'error': 'Invalid token'}), 401

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False, 'error': str(e)}), 500


@auth_bp.route('/link-account', methods=['POST'])
def link_account():
    """Link a Neon Auth account to an existing local user account"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        neon_auth_user_id = data.get('neon_auth_user_id')

        if not neon_auth_user_id:
            return jsonify({'error': 'No Neon Auth user ID provided'}), 400

        user_id = session.get('user_id')
        user = User.find_by_id(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        existing = User.find_by_neon_auth_id(neon_auth_user_id)
        if existing and existing.user_id != user.user_id:
            return jsonify({'error': 'This account is already linked to another user'}), 400

        user.neon_auth_user_id = neon_auth_user_id
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Account linked successfully'
        })

    except Exception as e:
        logger.error(f"Account linking error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/status')
def auth_status():
    """Check auth provider configuration status"""
    return jsonify({
        'neon_auth_configured': bool(current_app.config.get('NEON_AUTH_URL'))
    })


# =============================================================================
# NO ORGANIZATION PAGE
# =============================================================================

@auth_bp.route('/no-organization')
def no_organization():
    """Page shown when authenticated user has no tenant memberships"""
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('auth/no_organization.html')


# =============================================================================
# MULTI-TENANT ROUTES
# =============================================================================

@auth_bp.route('/select-tenant')
def select_tenant():
    """Tenant selection page - shown when user has multiple organizations"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('auth.login'))

    from app.services.tenant_service import TenantService
    tenant_service = TenantService()
    user_id = session.get('user_id')
    tenants = tenant_service.get_user_tenants(user_id)

    if not tenants:
        return redirect(url_for('auth.no_organization'))

    if len(tenants) == 1:
        tenant = tenants[0]
        session['current_tenant_id'] = tenant['tenant_id']
        session['current_tenant_slug'] = tenant['slug']
        session['current_tenant_name'] = tenant['name']
        session['current_role'] = tenant['role']
        return redirect(url_for('main.dashboard'))

    return render_template('auth/select_tenant.html', tenants=tenants)


@auth_bp.route('/switch-tenant', methods=['POST'])
def switch_tenant():
    """Switch active tenant context"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

    tenant_slug = request.form.get('tenant_slug') or (request.get_json(silent=True) or {}).get('tenant_slug')
    if not tenant_slug:
        flash('No organization specified', 'error')
        return redirect(url_for('auth.select_tenant'))

    from app.services.tenant_service import TenantService
    from app.models.tenant import Tenant

    tenant = Tenant.find_by_slug(tenant_slug)
    if not tenant:
        flash('Organization not found', 'error')
        return redirect(url_for('auth.select_tenant'))

    tenant_service = TenantService()
    user_tenants = tenant_service.get_user_tenants(session.get('user_id'))
    tenant_data = next((t for t in user_tenants if t['slug'] == tenant_slug), None)

    if not tenant_data:
        flash('You are not a member of this organization', 'error')
        return redirect(url_for('auth.select_tenant'))

    session['current_tenant_id'] = tenant_data['tenant_id']
    session['current_tenant_slug'] = tenant_data['slug']
    session['current_tenant_name'] = tenant_data['name']
    session['current_role'] = tenant_data['role']

    flash(f'Switched to {tenant_data["name"]}', 'success')
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/register-organization', methods=['GET', 'POST'])
def register_organization():
    """Register a new organization (tenant)"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        return render_template('auth/register_organization.html')

    from app.services.tenant_service import TenantService
    from app.utils.validators import sanitize_input

    name = sanitize_input(request.form.get('name', ''))
    business_type = sanitize_input(request.form.get('business_type', 'auto_repair'))
    email = sanitize_input(request.form.get('email', ''))
    phone = sanitize_input(request.form.get('phone', ''))

    if not name or len(name) < 2:
        flash('Organization name must be at least 2 characters', 'error')
        return render_template('auth/register_organization.html')

    tenant_service = TenantService()
    user_id = session.get('user_id')

    success, errors, tenant = tenant_service.create_tenant(
        name=name,
        owner_user_id=user_id,
        business_type=business_type,
        email=email or None,
        phone=phone or None,
    )

    if success:
        session['current_tenant_id'] = tenant.tenant_id
        session['current_tenant_slug'] = tenant.slug
        session['current_tenant_name'] = tenant.name
        session['current_role'] = 'owner'

        flash(f'Organization "{tenant.name}" created successfully!', 'success')
        return redirect(url_for('onboarding.step', step_number=1))
    else:
        for error in errors:
            flash(error, 'error')
        return render_template('auth/register_organization.html')
