"""
Authentication Routes Blueprint
Handles Neon Auth OAuth callbacks and session management
"""
from flask import Blueprint, request, redirect, url_for, jsonify, session, current_app
import logging
from app.services.auth_service import AuthService, neon_auth
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth_bp.route('/callback')
def callback():
    """
    OAuth callback handler for Neon Auth
    This is where users are redirected after OAuth sign-in
    """
    try:
        # Get session token from cookie (set by Neon Auth)
        session_token = request.cookies.get('better-auth.session_token')
        
        if not session_token:
            # Try to get from query params (some flows might use this)
            session_token = request.args.get('token')

        if session_token:
            # Verify the token with Neon Auth
            auth_service = AuthService()
            user = auth_service.authenticate_jwt(session_token)
            
            if user:
                # Set Flask session
                session['user_id'] = user.user_id
                session['username'] = user.username
                session['user_type'] = user.role
                session['logged_in'] = True
                session['auth_method'] = 'neon_auth'

                logger.info(f"User {user.username} authenticated via Neon Auth")

                # Redirect based on role
                if user.is_admin:
                    return redirect(url_for('administrator.dashboard'))
                else:
                    return redirect(url_for('technician.current_jobs'))
        
        # If no valid session, redirect to login with error
        logger.warning("OAuth callback without valid session")
        return redirect(url_for('main.login', error='auth_failed'))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(url_for('main.login', error='auth_error'))


@auth_bp.route('/neon-callback', methods=['POST'])
def neon_callback():
    """
    API endpoint for JavaScript client to notify backend of successful auth
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get('better-auth.session_token')
        
        if not session_token:
            return jsonify({'error': 'No session token'}), 401

        # Verify and get user
        auth_service = AuthService()
        user = auth_service.authenticate_jwt(session_token)

        if user:
            # Set Flask session
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['user_type'] = user.role
            session['logged_in'] = True
            session['auth_method'] = 'neon_auth'

            # Determine redirect URL
            redirect_url = '/technician/current_jobs'
            if user.is_admin:
                redirect_url = '/administrator/dashboard'

            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'redirect': redirect_url
            })

        return jsonify({'error': 'Invalid session'}), 401

    except Exception as e:
        logger.error(f"Neon callback error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/session')
def get_session():
    """
    Get current session info for the frontend
    """
    if session.get('logged_in'):
        return jsonify({
            'authenticated': True,
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('user_type'),
            'auth_method': session.get('auth_method', 'password')
        })
    
    return jsonify({'authenticated': False})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    API endpoint for logout (can be called from JavaScript)
    """
    try:
        auth_method = session.get('auth_method')
        
        # Clear Flask session
        session.clear()
        
        # If using Neon Auth, client should also sign out from Neon Auth
        response_data = {
            'success': True,
            'message': 'Logged out successfully'
        }
        
        if auth_method == 'neon_auth':
            # Include Neon Auth sign-out URL for client to call
            neon_auth_url = current_app.config.get('NEON_AUTH_URL', '')
            if neon_auth_url:
                response_data['neon_signout_url'] = f"{neon_auth_url}/sign-out"
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verify a Neon Auth JWT token
    Used by frontend to validate tokens
    """
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
    """
    Link a Neon Auth account to an existing local user account
    """
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

        # Check if this Neon Auth ID is already linked
        existing = User.find_by_neon_auth_id(neon_auth_user_id)
        if existing and existing.user_id != user.user_id:
            return jsonify({'error': 'This Neon Auth account is already linked to another user'}), 400

        # Link the account
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
