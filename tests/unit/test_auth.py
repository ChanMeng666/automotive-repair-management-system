"""
Unit tests for authentication service and user model
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing functionality (werkzeug utility)"""

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

    def test_user_is_admin_superadmin(self):
        """Test is_admin returns True for superadmins"""
        from app.models.user import User

        superadmin = User(username='superadmin', is_superadmin=True, is_active=True)
        regular = User(username='regular', is_superadmin=False, is_active=True)

        assert superadmin.is_admin is True
        assert regular.is_admin is False

    def test_user_is_admin_not_based_on_role(self):
        """Test is_admin does not check legacy role column"""
        from app.models.user import User

        # Legacy role='administrator' should NOT make user admin
        user = User(username='admin', role='administrator', is_superadmin=False, is_active=True)
        assert user.is_admin is False

    def test_user_password_hash_nullable(self):
        """Test that user can be created without password_hash (Neon Auth users)"""
        from app.models.user import User

        user = User(username='neon_user', email='test@example.com', is_active=True)
        assert user.password_hash is None

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

        user = User(username='testuser')
        repr_str = repr(user)
        assert 'testuser' in repr_str

    def test_user_email_verified_default(self):
        """Test email_verified can be set"""
        from app.models.user import User

        user = User(username='test', is_active=True, email_verified=False)
        assert user.email_verified is False

        user2 = User(username='test2', is_active=True, email_verified=True)
        assert user2.email_verified is True


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
            session['current_role'] = 'technician'
            with pytest.raises(Forbidden):
                admin_route()

    def test_admin_required_allows_owner(self, app):
        """Test admin_required allows owner role"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_route():
            return "admin access"

        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['current_role'] = 'owner'
            result = admin_route()
            assert result == "admin access"

    def test_admin_required_allows_admin(self, app):
        """Test admin_required allows admin role"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_route():
            return "admin access"

        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['current_role'] = 'admin'
            result = admin_route()
            assert result == "admin access"

    def test_technician_required_allows_technician(self, app):
        """Test technician_required allows technician role"""
        from app.utils.decorators import technician_required

        @technician_required
        def tech_route():
            return "tech access"

        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['current_role'] = 'technician'
            result = tech_route()
            assert result == "tech access"

    def test_technician_required_denies_viewer(self, app):
        """Test technician_required denies viewer role"""
        from werkzeug.exceptions import Forbidden
        from app.utils.decorators import technician_required

        @technician_required
        def tech_route():
            return "tech access"

        with app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['current_role'] = 'viewer'
            with pytest.raises(Forbidden):
                tech_route()
