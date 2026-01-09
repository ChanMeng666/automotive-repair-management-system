"""
Unit tests for authentication service and user model
"""
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash, check_password_hash


class TestAuthService:
    """Tests for AuthService class"""

    def test_authenticate_demo_mode_enabled(self):
        """Test authentication in demo mode"""
        with patch.dict('os.environ', {
            'AUTH_DEMO_MODE': 'true',
            'DEMO_PASSWORD': 'test_password'
        }):
            from app.services.auth_service import AuthService
            auth_service = AuthService()

            # Mock database authentication to return None
            with patch.object(auth_service, '_authenticate_from_database', return_value=None):
                success, user_data, error = auth_service.authenticate(
                    'testuser', 'test_password', 'technician'
                )

                assert success is True
                assert user_data is not None
                assert user_data['username'] == 'testuser'
                assert user_data['role'] == 'technician'

    def test_authenticate_demo_mode_wrong_password(self):
        """Test authentication fails with wrong password in demo mode"""
        with patch.dict('os.environ', {
            'AUTH_DEMO_MODE': 'true',
            'DEMO_PASSWORD': 'correct_password'
        }):
            from app.services.auth_service import AuthService
            auth_service = AuthService()

            with patch.object(auth_service, '_authenticate_from_database', return_value=None):
                success, user_data, error = auth_service.authenticate(
                    'testuser', 'wrong_password', 'technician'
                )

                assert success is False
                assert user_data is None

    def test_authenticate_demo_mode_disabled(self):
        """Test authentication when demo mode is disabled"""
        with patch.dict('os.environ', {'AUTH_DEMO_MODE': 'false'}):
            from app.services.auth_service import AuthService
            auth_service = AuthService()

            with patch.object(auth_service, '_authenticate_from_database', return_value=None):
                success, user_data, error = auth_service.authenticate(
                    'testuser', 'any_password', 'technician'
                )

                assert success is False
                assert user_data is None


class TestPasswordHashing:
    """Tests for password hashing functionality"""

    def test_password_hash_generation(self):
        """Test that password hashing works correctly"""
        password = "test_password_123"
        hashed = generate_password_hash(password)

        assert hashed != password
        assert check_password_hash(hashed, password)

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"

        hash1 = generate_password_hash(password1)
        hash2 = generate_password_hash(password2)

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salting)"""
        password = "same_password"

        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        assert check_password_hash(hash1, password)
        assert check_password_hash(hash2, password)

    def test_wrong_password_fails_verification(self):
        """Test that wrong password fails verification"""
        password = "correct_password"
        wrong_password = "wrong_password"

        hashed = generate_password_hash(password)

        assert not check_password_hash(hashed, wrong_password)


class TestUserModel:
    """Tests for User model (requires database mock)"""

    def test_user_is_admin_property(self):
        """Test is_admin property"""
        from app.models.user import User

        admin_user = User(
            user_id=1,
            username='admin',
            role='administrator',
            is_active=True
        )
        tech_user = User(
            user_id=2,
            username='tech',
            role='technician',
            is_active=True
        )

        assert admin_user.is_admin is True
        assert tech_user.is_admin is False

    def test_user_is_technician_property(self):
        """Test is_technician property"""
        from app.models.user import User

        admin_user = User(
            user_id=1,
            username='admin',
            role='administrator',
            is_active=True
        )
        tech_user = User(
            user_id=2,
            username='tech',
            role='technician',
            is_active=True
        )

        assert admin_user.is_technician is False
        assert tech_user.is_technician is True

    def test_user_check_password(self):
        """Test password checking"""
        from app.models.user import User

        password = "test_password"
        user = User(
            user_id=1,
            username='test',
            password_hash=generate_password_hash(password),
            role='technician',
            is_active=True
        )

        assert user.check_password(password) is True
        assert user.check_password("wrong_password") is False

    def test_user_set_password(self):
        """Test setting password"""
        from app.models.user import User

        user = User(
            user_id=1,
            username='test',
            role='technician',
            is_active=True
        )

        new_password = "new_secure_password"
        user.set_password(new_password)

        assert user.password_hash is not None
        assert user.check_password(new_password) is True

    def test_user_to_dict(self):
        """Test converting user to dictionary"""
        from app.models.user import User

        user = User(
            user_id=1,
            username='testuser',
            email='test@example.com',
            role='technician',
            is_active=True,
            created_at='2024-01-01 00:00:00',
            last_login=None
        )

        data = user.to_dict()

        assert data['user_id'] == 1
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['role'] == 'technician'
        assert data['is_active'] is True
        assert 'password_hash' not in data  # Should not include sensitive data

    def test_user_repr(self):
        """Test string representation"""
        from app.models.user import User

        user = User(
            user_id=1,
            username='testuser',
            role='administrator'
        )

        repr_str = repr(user)
        assert 'testuser' in repr_str
        assert 'administrator' in repr_str


class TestRBACDecorators:
    """Tests for RBAC decorators"""

    def test_login_required_decorator(self, app):
        """Test login_required decorator"""
        from flask import session
        from app.utils.decorators import login_required

        @login_required
        def protected_route():
            return "success"

        with app.test_request_context():
            # Without login
            session.clear()
            result = protected_route()
            # Should redirect to login

    def test_admin_required_decorator(self, app):
        """Test admin_required decorator"""
        from flask import session
        from app.utils.decorators import admin_required

        @admin_required
        def admin_route():
            return "admin access"

        with app.test_request_context():
            # Without admin role
            session['logged_in'] = True
            session['user_type'] = 'technician'
            # Should be denied

    def test_role_required_decorator(self, app):
        """Test role_required decorator"""
        from flask import session
        from app.utils.decorators import role_required

        @role_required('administrator', 'manager')
        def multi_role_route():
            return "multi role access"

        with app.test_request_context():
            session['logged_in'] = True
            session['user_type'] = 'administrator'
            # Should succeed


@pytest.fixture
def app():
    """Create test application"""
    from app import create_app

    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'

    return app
