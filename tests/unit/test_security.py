"""
Security Module Unit Tests
Tests for CSRF protection, password security, input validation, SQL injection prevention
"""
import pytest
from unittest.mock import Mock, patch
import secrets
import html

from app.utils.security import (
    CSRFProtection, PasswordSecurity, InputSanitizer,
    SQLInjectionProtection, SessionSecurity, SecurityConfig,
    csrf_protect, require_auth
)


@pytest.mark.unit
@pytest.mark.security
class TestPasswordSecurity:
    """Password security tests"""

    def test_hash_password_generates_different_hashes(self):
        """Same password should generate different hashes due to random salt"""
        password = "test123456"

        hash1, salt1 = PasswordSecurity.hash_password(password)
        hash2, salt2 = PasswordSecurity.hash_password(password)

        assert hash1 != hash2
        assert salt1 != salt2
        assert len(hash1) == 64  # SHA256 hex length
        assert len(salt1) == 32  # 16-byte salt hex length

    def test_hash_password_with_custom_salt(self):
        """Password hash with custom salt should be deterministic"""
        password = "test123456"
        custom_salt = "custom_salt_value"

        hash1, salt1 = PasswordSecurity.hash_password(password, custom_salt)
        hash2, salt2 = PasswordSecurity.hash_password(password, custom_salt)

        assert hash1 == hash2  # Same password + salt = same hash
        assert salt1 == salt2 == custom_salt

    def test_verify_password_correct(self):
        """Correct password should verify successfully"""
        password = "test123456"
        hash_value, salt = PasswordSecurity.hash_password(password)

        assert PasswordSecurity.verify_password(password, hash_value, salt) is True

    def test_verify_password_incorrect(self):
        """Wrong password should fail verification"""
        password = "test123456"
        wrong_password = "wrong123456"
        hash_value, salt = PasswordSecurity.hash_password(password)

        assert PasswordSecurity.verify_password(wrong_password, hash_value, salt) is False

    def test_verify_password_exception_handling(self):
        """Password verification should return False on exceptions"""
        with patch('app.utils.security.PasswordSecurity.hash_password', side_effect=Exception("Test error")):
            result = PasswordSecurity.verify_password("test", "hash", "salt")
            assert result is False


@pytest.mark.unit
@pytest.mark.security
class TestInputSanitizer:
    """Input sanitizer tests"""

    def test_sanitize_string_basic(self):
        """HTML tags should be escaped"""
        dirty_input = "  <script>alert('xss')</script>  "
        clean_output = InputSanitizer.sanitize_string(dirty_input)

        assert clean_output == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_sanitize_string_max_length(self):
        """String should be truncated to max_length"""
        long_input = "a" * 300
        clean_output = InputSanitizer.sanitize_string(long_input, max_length=100)

        assert len(clean_output) == 100

    def test_sanitize_string_non_string_input(self):
        """Non-string input should return empty string"""
        assert InputSanitizer.sanitize_string(123) == ""
        assert InputSanitizer.sanitize_string(None) == ""
        assert InputSanitizer.sanitize_string([]) == ""

    def test_validate_email_valid(self):
        """Valid emails should pass validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "firstname+lastname@company.org"
        ]

        for email in valid_emails:
            assert InputSanitizer.validate_email(email) is True

    def test_validate_email_invalid(self):
        """Invalid emails should fail validation"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            "a" * 250 + "@domain.com"
        ]

        for email in invalid_emails:
            assert InputSanitizer.validate_email(email) is False

    def test_validate_phone_valid_mobile(self):
        """Valid mobile numbers should pass validation"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18699999999"
        ]

        for phone in valid_phones:
            assert InputSanitizer.validate_phone(phone) is True

    def test_validate_phone_valid_landline(self):
        """Valid landline numbers should pass validation"""
        valid_landlines = [
            "010-12345678",
            "021-87654321",
            "0755-88888888"
        ]

        for phone in valid_landlines:
            assert InputSanitizer.validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """Invalid phone numbers should fail validation"""
        invalid_phones = [
            "12345",
            "abc123",
            "11112345678",
            "999999999999"
        ]

        for phone in invalid_phones:
            assert InputSanitizer.validate_phone(phone) is False


@pytest.mark.unit
@pytest.mark.security
class TestSQLInjectionProtection:
    """SQL injection protection tests"""

    def test_scan_safe_input(self):
        """Safe input should not be flagged"""
        safe_inputs = [
            "John Doe",
            "Normal text content",
            "123456",
            "user@example.com"
        ]

        for input_str in safe_inputs:
            assert SQLInjectionProtection.scan_sql_injection(input_str) is False

    def test_scan_dangerous_keywords(self):
        """Dangerous SQL keywords should be detected"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1 UNION SELECT * FROM users",
            "admin'--",
            "1 OR 1=1",
            "EXEC xp_cmdshell"
        ]

        for input_str in dangerous_inputs:
            assert SQLInjectionProtection.scan_sql_injection(input_str) is True

    def test_scan_non_string_input(self):
        """Non-string input should return False"""
        assert SQLInjectionProtection.scan_sql_injection(123) is False
        assert SQLInjectionProtection.scan_sql_injection(None) is False
        assert SQLInjectionProtection.scan_sql_injection([]) is False


@pytest.mark.unit
@pytest.mark.security
class TestCSRFProtection:
    """CSRF protection tests"""

    def test_generate_token(self, app):
        """CSRF token should be generated and stored in session"""
        with app.test_request_context():
            from flask import session
            token = CSRFProtection.generate_token()
            assert token is not None
            assert len(token) > 20

    def test_validate_token_valid(self, app):
        """Valid token should pass validation"""
        with app.test_request_context():
            from flask import session
            token = CSRFProtection.generate_token()
            assert CSRFProtection.validate_token(token) is True

    def test_validate_token_invalid(self, app):
        """Invalid token should fail validation"""
        with app.test_request_context():
            from flask import session
            CSRFProtection.generate_token()
            assert CSRFProtection.validate_token('wrong_token') is False
            assert CSRFProtection.validate_token('') is False
            assert CSRFProtection.validate_token(None) is False


@pytest.mark.unit
@pytest.mark.security
class TestSessionSecurity:
    """Session security tests"""

    def test_generate_session_id(self):
        """Session IDs should be unique"""
        session_id1 = SessionSecurity.generate_session_id()
        session_id2 = SessionSecurity.generate_session_id()

        assert len(session_id1) > 20
        assert len(session_id2) > 20
        assert session_id1 != session_id2


@pytest.mark.unit
@pytest.mark.security
class TestSecurityConfig:
    """Security configuration tests"""

    def test_apply_security_headers(self):
        """Security headers should be applied to response"""
        mock_response = Mock()
        mock_response.headers = {}

        result = SecurityConfig.apply_security_headers(mock_response)

        assert result == mock_response
        assert 'X-Content-Type-Options' in mock_response.headers
        assert 'X-Frame-Options' in mock_response.headers
        assert 'X-XSS-Protection' in mock_response.headers
        assert mock_response.headers['X-Content-Type-Options'] == 'nosniff'


@pytest.mark.unit
@pytest.mark.security
class TestSecurityDecorators:
    """Security decorator tests"""

    def test_csrf_protect_get_request(self, app):
        """GET requests should not require CSRF validation"""
        with app.test_request_context(method='GET'):
            mock_func = Mock(return_value="success")
            decorated_func = csrf_protect(mock_func)
            result = decorated_func()
            assert result == "success"
            mock_func.assert_called_once()

    def test_csrf_protect_post_valid_token(self, app):
        """POST with valid CSRF token should succeed"""
        with app.test_request_context(method='POST', data={'csrf_token': 'test'}):
            from flask import session
            session['csrf_token'] = 'test'

            mock_func = Mock(return_value="success")
            with patch.object(CSRFProtection, 'validate_token', return_value=True):
                decorated_func = csrf_protect(mock_func)
                result = decorated_func()
                assert result == "success"

    def test_csrf_protect_post_invalid_token(self, app):
        """POST with invalid CSRF token should abort 403"""
        from werkzeug.exceptions import Forbidden
        with app.test_request_context(method='POST', data={'csrf_token': 'bad'}):
            mock_func = Mock()
            with patch.object(CSRFProtection, 'validate_token', return_value=False):
                decorated_func = csrf_protect(mock_func)
                with pytest.raises(Forbidden):
                    decorated_func()
                mock_func.assert_not_called()

    def test_require_auth_logged_in_user(self, app):
        """Logged-in user should access protected resource"""
        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['user_type'] = 'technician'
            session['user_id'] = 'test_user'

            mock_func = Mock(return_value="success")
            with patch.object(SessionSecurity, 'validate_session', return_value=True), \
                 patch.object(SessionSecurity, 'update_session_activity'):
                decorated_func = require_auth()(mock_func)
                result = decorated_func()
                assert result == "success"

    def test_require_auth_not_logged_in(self, app):
        """Unauthenticated user should be denied access"""
        from werkzeug.exceptions import Unauthorized
        with app.test_request_context():
            mock_func = Mock()
            decorated_func = require_auth()(mock_func)
            with pytest.raises(Unauthorized):
                decorated_func()
            mock_func.assert_not_called()

    def test_require_auth_insufficient_permissions(self, app):
        """User with wrong role should be denied access"""
        from werkzeug.exceptions import Forbidden
        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['user_type'] = 'technician'

            mock_func = Mock()
            decorated_func = require_auth(['administrator'])(mock_func)
            with pytest.raises(Forbidden):
                decorated_func()
            mock_func.assert_not_called()
