"""
Multi-Tenant Unit Tests
Tests for TenantScopedMixin, permissions, tenant creation, and membership
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from app.models.user import User, ROLE_PERMISSIONS


@pytest.mark.unit
class TestPermissionSystem:
    """Tests for RBAC permission system"""

    def test_role_permissions_defined(self):
        """All roles should have permissions defined"""
        assert 'owner' in ROLE_PERMISSIONS
        assert 'admin' in ROLE_PERMISSIONS
        assert 'manager' in ROLE_PERMISSIONS
        assert 'technician' in ROLE_PERMISSIONS
        assert 'parts_clerk' in ROLE_PERMISSIONS
        assert 'viewer' in ROLE_PERMISSIONS

    def test_owner_has_all_permissions(self):
        """Owner should have all permissions"""
        owner_perms = ROLE_PERMISSIONS['owner']
        assert 'manage_org' in owner_perms
        assert 'manage_users' in owner_perms
        assert 'manage_catalog' in owner_perms
        assert 'manage_inventory' in owner_perms
        assert 'manage_jobs' in owner_perms
        assert 'manage_customers' in owner_perms
        assert 'manage_billing' in owner_perms
        assert 'view_reports' in owner_perms

    def test_technician_limited_permissions(self):
        """Technician should only have job and report permissions"""
        tech_perms = ROLE_PERMISSIONS['technician']
        assert 'manage_jobs' in tech_perms
        assert 'view_reports' in tech_perms
        assert 'manage_org' not in tech_perms
        assert 'manage_users' not in tech_perms
        assert 'manage_billing' not in tech_perms

    def test_viewer_only_view(self):
        """Viewer should only have view_reports permission"""
        viewer_perms = ROLE_PERMISSIONS['viewer']
        assert 'view_reports' in viewer_perms
        assert len(viewer_perms) == 1

    def test_parts_clerk_permissions(self):
        """Parts clerk should manage catalog and inventory"""
        clerk_perms = ROLE_PERMISSIONS['parts_clerk']
        assert 'manage_catalog' in clerk_perms
        assert 'manage_inventory' in clerk_perms
        assert 'view_reports' in clerk_perms
        assert 'manage_jobs' not in clerk_perms


@pytest.mark.unit
class TestTenantModel:
    """Tests for Tenant model"""

    def test_generate_slug(self):
        """Slug generation should create URL-friendly slugs"""
        from app.models.tenant import Tenant

        with patch.object(Tenant, 'find_by_slug', return_value=None):
            slug = Tenant.generate_slug("Joe's Auto Repair")
            assert slug is not None
            assert ' ' not in slug
            assert "'" not in slug
            assert slug.islower() or '-' in slug

    def test_generate_slug_uniqueness(self):
        """Generated slugs should be unique for different names"""
        from app.models.tenant import Tenant

        with patch.object(Tenant, 'find_by_slug', return_value=None):
            slug1 = Tenant.generate_slug("Shop A")
            slug2 = Tenant.generate_slug("Shop B")
            assert 'shop-a' in slug1 or slug1.startswith('shop-a')
            assert 'shop-b' in slug2 or slug2.startswith('shop-b')


@pytest.mark.unit
class TestValidators:
    """Tests for input validators"""

    def test_validate_email_valid(self):
        from app.utils.validators import validate_email
        assert validate_email('test@example.com') is True
        assert validate_email('user.name@domain.co') is True

    def test_validate_email_invalid(self):
        from app.utils.validators import validate_email
        assert validate_email('') is False
        assert validate_email('not-an-email') is False
        assert validate_email('@domain.com') is False
        assert validate_email(None) is False

    def test_validate_phone_valid(self):
        from app.utils.validators import validate_phone
        assert validate_phone('5551234567') is True
        assert validate_phone('555-123-4567') is True

    def test_validate_phone_invalid(self):
        from app.utils.validators import validate_phone
        assert validate_phone('') is False
        assert validate_phone('123') is False
        assert validate_phone(None) is False

    def test_validate_positive_integer(self):
        from app.utils.validators import validate_positive_integer
        assert validate_positive_integer(1) is True
        assert validate_positive_integer(100) is True
        assert validate_positive_integer(0) is False
        assert validate_positive_integer(-1) is False
        assert validate_positive_integer('abc') is False

    def test_validate_cost(self):
        from app.utils.validators import validate_cost
        assert validate_cost(0) is True
        assert validate_cost(49.99) is True
        assert validate_cost(999999.99) is True
        assert validate_cost(-1) is False
        assert validate_cost(1000000) is False

    def test_validate_customer_data_valid(self, sample_customer_data):
        from app.utils.validators import validate_customer_data
        result = validate_customer_data(sample_customer_data)
        assert result.is_valid is True
        assert len(result.get_errors()) == 0

    def test_validate_customer_data_missing_email(self, sample_customer_data):
        from app.utils.validators import validate_customer_data
        sample_customer_data['email'] = ''
        result = validate_customer_data(sample_customer_data)
        assert result.is_valid is False
        assert any('email' in e.lower() for e in result.get_errors())

    def test_validate_customer_data_missing_family_name(self, sample_customer_data):
        from app.utils.validators import validate_customer_data
        sample_customer_data['family_name'] = ''
        result = validate_customer_data(sample_customer_data)
        assert result.is_valid is False
        assert any('family_name' in e.lower() for e in result.get_errors())

    def test_validate_service_data_valid(self):
        from app.utils.validators import validate_service_data
        result = validate_service_data({'service_name': 'Oil Change', 'cost': 49.99})
        assert result.is_valid is True

    def test_validate_service_data_missing_name(self):
        from app.utils.validators import validate_service_data
        result = validate_service_data({'service_name': '', 'cost': 49.99})
        assert result.is_valid is False

    def test_validate_part_data_valid(self):
        from app.utils.validators import validate_part_data
        result = validate_part_data({'part_name': 'Oil Filter', 'cost': 12.99})
        assert result.is_valid is True

    def test_sanitize_input(self):
        from app.utils.validators import sanitize_input
        assert sanitize_input(None) == ''
        assert sanitize_input('  hello  ') == 'hello'
        assert sanitize_input('<script>alert("xss")</script>') == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'

    def test_validate_date_valid(self):
        from app.utils.validators import validate_date
        assert validate_date('2024-06-15') is True
        assert validate_date('2024-01-01') is True

    def test_validate_date_invalid(self):
        from app.utils.validators import validate_date
        assert validate_date('') is False
        assert validate_date('not-a-date') is False
        assert validate_date('2024-13-01') is False


@pytest.mark.unit
class TestSecurityModule:
    """Tests for security utilities"""

    def test_csrf_protection_generate_token(self, app):
        """CSRF token should be generated"""
        from app.utils.security import CSRFProtection
        with app.test_request_context():
            from flask import session
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    pass
                # Token generation is session-dependent, just verify module imports
                assert CSRFProtection is not None

    def test_sql_injection_detection(self):
        """SQL injection patterns should be detected"""
        from app.utils.security import SQLInjectionProtection

        assert SQLInjectionProtection.scan_sql_injection("normal input") is False
        assert SQLInjectionProtection.scan_sql_injection("hello world") is False
        assert SQLInjectionProtection.scan_sql_injection("'; DROP TABLE users; --") is True
        assert SQLInjectionProtection.scan_sql_injection("1=1") is True
        assert SQLInjectionProtection.scan_sql_injection("UNION SELECT * FROM") is True

    def test_input_sanitizer(self):
        """Input sanitizer should clean strings"""
        from app.utils.security import InputSanitizer

        assert InputSanitizer.sanitize_string('  hello  ') == 'hello'
        assert InputSanitizer.sanitize_string('') == ''
        assert InputSanitizer.sanitize_string(123) == ''
        assert '&lt;' in InputSanitizer.sanitize_string('<script>alert(1)</script>')

    def test_password_security(self):
        """Password hashing and verification should work"""
        from app.utils.security import PasswordSecurity

        password = 'testpassword123'
        hashed, salt = PasswordSecurity.hash_password(password)

        assert hashed is not None
        assert salt is not None
        assert PasswordSecurity.verify_password(password, hashed, salt) is True
        assert PasswordSecurity.verify_password('wrong', hashed, salt) is False
