"""
pytest Configuration
Defines test fixtures and global test configuration
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from flask import Flask

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.base import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create test Flask application instance"""
    app = create_app('testing')
    app.config.from_object(TestingConfig)

    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'DB_NAME': 'spb_test',
        'LOG_LEVEL': 'ERROR',
    })

    return app


@pytest.fixture
def client(app):
    """Create a fresh test client per test"""
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_customer_data():
    """Sample customer data"""
    return {
        'first_name': 'John',
        'family_name': 'Smith',
        'email': 'john.smith@example.com',
        'phone': '5551234567',
    }


@pytest.fixture
def sample_job_data():
    """Sample job data"""
    return {
        'job_id': 1,
        'customer_id': 1,
        'job_date': '2024-06-15',
        'completed': False,
        'paid': False,
        'total_cost': 250.00,
    }


@pytest.fixture
def sample_service_data():
    """Sample service data"""
    return {
        'service_id': 1,
        'service_name': 'Oil Change',
        'cost': 49.99,
        'category': 'Maintenance',
        'estimated_duration_minutes': 30,
    }


@pytest.fixture
def sample_part_data():
    """Sample part data"""
    return {
        'part_id': 1,
        'part_name': 'Oil Filter',
        'cost': 12.99,
        'sku': 'OIL-FLT-001',
        'category': 'Filters',
        'supplier': 'AutoZone',
    }


@pytest.fixture
def authenticated_session(app):
    """Authenticated technician session (fresh client)"""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
        sess['username'] = 'test_user'
        sess['logged_in'] = True
        sess['current_tenant_id'] = 1
        sess['current_tenant_slug'] = 'test-org'
        sess['current_tenant_name'] = 'Test Organization'
        sess['current_role'] = 'technician'
    return client


@pytest.fixture
def admin_session(app):
    """Administrator session (fresh client)"""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin_user'
        sess['username'] = 'admin_user'
        sess['logged_in'] = True
        sess['current_tenant_id'] = 1
        sess['current_tenant_slug'] = 'test-org'
        sess['current_tenant_name'] = 'Test Organization'
        sess['current_role'] = 'owner'
    return client


# Test markers
pytest_plugins = []


def pytest_configure(config):
    """pytest configuration"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests")
