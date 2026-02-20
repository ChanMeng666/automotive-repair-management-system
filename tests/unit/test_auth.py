"""
Unit tests for authentication service and user model
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.mark.unit
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
        hash1 = generate_password_hash("password1")
        hash2 = generate_password_hash("password2")
        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salting)"""
        password = "same_password"
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)

        assert hash1 != hash2
        assert check_password_hash(hash1, password)
        assert check_password_hash(hash2, password)

    def test_wrong_password_fails_verification(self):
        """Test that wrong password fails verification"""
        hashed = generate_password_hash("correct_password")
        assert not check_password_hash(hashed, "wrong_password")


@pytest.mark.unit
class TestUserModel:
    """Tests for User model"""

    def test_user_is_admin_property(self):
        """Test is_admin property"""
        from app.models.user import User

        admin_user = User(username='admin', role='administrator', is_active=True)
        tech_user = User(username='tech', role='technician', is_active=True)

        assert admin_user.is_admin is True
        assert tech_user.is_admin is False

    def test_user_is_technician_property(self):
        """Test is_technician property"""
        from app.models.user import User

        admin_user = User(username='admin', role='administrator', is_active=True)
        tech_user = User(username='tech', role='technician', is_active=True)

        assert admin_user.is_technician is False
        assert tech_user.is_technician is True

    def test_user_check_password(self):
        """Test password checking"""
        from app.models.user import User

        password = "test_password"
        user = User(
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

        user = User(username='test', role='technician', is_active=True)
        new_password = "new_secure_password"
        user.set_password(new_password)

        assert user.password_hash is not None
        assert user.check_password(new_password) is True

    def test_user_to_dict(self):
        """Test converting user to dictionary"""
        from app.models.user import User

        user = User(
            username='testuser',
            email='test@example.com',
            is_active=True,
            created_at=datetime(2024, 1, 1),
        )

        data = user.to_dict()

        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['is_active'] is True
        assert 'password_hash' not in data

    def test_user_repr(self):
        """Test string representation"""
        from app.models.user import User

        user = User(username='testuser', role='administrator')
        repr_str = repr(user)
        assert 'testuser' in repr_str


@pytest.mark.unit
class TestRBACDecorators:
    """Tests for RBAC decorators"""

    def test_login_required_decorator(self, app):
        """Test login_required redirects unauthenticated users"""
        from app.utils.decorators import login_required

        @login_required
        def protected_route():
            return "success"

        with app.test_request_context():
            from flask import session
            session.clear()
            result = protected_route()
            # Should redirect to login (302 response)
            assert result.status_code in (302, 303) or hasattr(result, 'location')

    def test_admin_required_decorator(self, app):
        """Test admin_required denies non-admin users"""
        from werkzeug.exceptions import Forbidden
        from app.utils.decorators import admin_required

        @admin_required
        def admin_route():
            return "admin access"

        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['user_type'] = 'technician'
            with pytest.raises(Forbidden):
                admin_route()
