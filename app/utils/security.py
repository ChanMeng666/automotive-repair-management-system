"""
Security Management Module
Provides CSRF protection, password hashing, input validation, SQL injection prevention
"""
import secrets
import hashlib
import hmac
import re
import html
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
from flask import session, request, abort
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF token protection"""

    @staticmethod
    def generate_token() -> str:
        """Generate a CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']

    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate a CSRF token"""
        if 'csrf_token' not in session:
            return False

        stored_token = session.get('csrf_token')
        if not stored_token or not token:
            return False

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(stored_token, token)

    @staticmethod
    def get_token() -> str:
        """Get the current CSRF token"""
        return session.get('csrf_token', '')


class PasswordSecurity:
    """Password security management"""

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )

        return password_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password"""
        try:
            computed_hash, _ = PasswordSecurity.hash_password(password, salt)
            return hmac.compare_digest(stored_hash, computed_hash)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False


class InputSanitizer:
    """Input data sanitization and validation"""

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""

        cleaned = input_str.strip()

        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]

        cleaned = html.escape(cleaned, quote=True)

        return cleaned

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False

        cleaned_phone = re.sub(r'[^\d]', '', phone)

        if re.match(r'^1[3-9]\d{9}$', cleaned_phone):
            return True

        if re.match(r'^0\d{2,3}-?\d{7,8}$', phone):
            return True

        return False


class SQLInjectionProtection:
    """SQL injection prevention"""

    DANGEROUS_KEYWORDS = [
        'union', 'select', 'insert', 'update', 'delete', 'drop', 'create',
        'alter', 'exec', 'execute', '--', '/*', '*/', '1=1', 'or 1=1'
    ]

    @staticmethod
    def scan_sql_injection(input_str: str) -> bool:
        """Scan for SQL injection attacks"""
        if not isinstance(input_str, str):
            return False

        lower_input = input_str.lower()

        for keyword in SQLInjectionProtection.DANGEROUS_KEYWORDS:
            if keyword in lower_input:
                logger.warning(f"Potential SQL injection detected: {keyword}")
                return True

        return False


class SessionSecurity:
    """Session security management"""

    @staticmethod
    def generate_session_id() -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_session(user_id: str, ip_address: str) -> bool:
        """Validate session security"""
        if 'user_id' not in session:
            return False

        if session.get('user_id') != user_id:
            return False

        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_time > timedelta(hours=24):
                    return False
            except ValueError:
                return False

        return True

    @staticmethod
    def update_session_activity():
        """Update session activity timestamp"""
        session['last_activity'] = datetime.now().isoformat()


# Decorator functions
def csrf_protect(f):
    """CSRF protection decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')

            if not token or not CSRFProtection.validate_token(token):
                logger.warning(f"CSRF attack attempt: {request.remote_addr}")
                abort(403, description="Invalid CSRF token")

        return f(*args, **kwargs)
    return decorated_function


def require_auth(user_types: List[str] = None):
    """Authentication required decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                abort(401, description="Login required")

            if user_types:
                user_type = session.get('current_role')
                if user_type not in user_types:
                    abort(403, description="Insufficient permissions")

            user_id = session.get('user_id')
            ip_address = request.remote_addr

            if not SessionSecurity.validate_session(user_id, ip_address):
                session.clear()
                abort(401, description="Session invalid, please log in again")

            SessionSecurity.update_session_activity()

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Security configuration
class SecurityConfig:
    """Security configuration"""

    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    @classmethod
    def apply_security_headers(cls, response):
        """Apply security headers"""
        for header, value in cls.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
