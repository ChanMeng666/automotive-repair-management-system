"""
Test Utilities Module
Provides common test helper functions and tools
"""
import json
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock


def create_mock_customer(customer_id: int = 1, **kwargs) -> Mock:
    """Create a mock customer object"""
    default_data = {
        'customer_id': customer_id,
        'first_name': 'John',
        'family_name': 'Smith',
        'full_name': 'John Smith',
        'email': f'customer{customer_id}@example.com',
        'phone': '5551234567',
        'address': '123 Main Street, Springfield, IL 62701',
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }
    default_data.update(kwargs)

    mock_customer = Mock()
    for key, value in default_data.items():
        setattr(mock_customer, key, value)

    return mock_customer


def create_mock_job(job_id: int = 1, customer_id: int = 1, **kwargs) -> Mock:
    """Create a mock job object"""
    default_data = {
        'job_id': job_id,
        'customer_id': customer_id,
        'vehicle_info': '2020 Toyota Camry',
        'problem_description': 'Engine noise',
        'status': 'in_progress',
        'total_cost': 1500.00,
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }
    default_data.update(kwargs)

    mock_job = Mock()
    for key, value in default_data.items():
        setattr(mock_job, key, value)

    return mock_job


def create_mock_service(service_id: int = 1, **kwargs) -> Mock:
    """Create a mock service object"""
    default_data = {
        'service_id': service_id,
        'service_name': 'Engine Repair',
        'description': 'Inspect and repair engine issues',
        'base_price': 800.00,
        'estimated_hours': 4.0
    }
    default_data.update(kwargs)

    mock_service = Mock()
    for key, value in default_data.items():
        setattr(mock_service, key, value)

    return mock_service


def create_mock_part(part_id: int = 1, **kwargs) -> Mock:
    """Create a mock part object"""
    default_data = {
        'part_id': part_id,
        'part_name': 'Oil Filter',
        'part_number': 'OF-001',
        'price': 45.00,
        'supplier': 'Toyota OEM',
        'stock_quantity': 50
    }
    default_data.update(kwargs)

    mock_part = Mock()
    for key, value in default_data.items():
        setattr(mock_part, key, value)

    return mock_part


def assert_json_response(response, expected_status: int = 200, expected_keys: Optional[list] = None):
    """Assert JSON response format and content"""
    assert response.status_code == expected_status
    assert response.content_type == 'application/json'

    data = json.loads(response.data)

    if expected_keys:
        for key in expected_keys:
            assert key in data

    return data


def assert_redirect_response(response, expected_location: str = None):
    """Assert redirect response"""
    assert response.status_code in [301, 302, 303, 307, 308]

    if expected_location:
        assert expected_location in response.location

    return response.location


def create_test_form_data(base_data: Dict[str, Any], csrf_token: str = 'test_token') -> Dict[str, Any]:
    """Create test form data with CSRF token"""
    form_data = base_data.copy()
    form_data['csrf_token'] = csrf_token
    return form_data


class MockDatabaseCursor:
    """Mock database cursor"""

    def __init__(self, fetch_data: Any = None, rowcount: int = 0):
        self.fetch_data = fetch_data
        self.rowcount = rowcount
        self.executed_queries = []

    def execute(self, query: str, params: tuple = None):
        """Mock query execution"""
        self.executed_queries.append((query, params))

    def fetchone(self):
        """Mock fetch one row"""
        return self.fetch_data if not isinstance(self.fetch_data, list) else (
            self.fetch_data[0] if self.fetch_data else None
        )

    def fetchall(self):
        """Mock fetch all rows"""
        return self.fetch_data if isinstance(self.fetch_data, list) else (
            [self.fetch_data] if self.fetch_data else []
        )

    def close(self):
        """Mock close cursor"""
        pass


class MockDatabaseConnection:
    """Mock database connection"""

    def __init__(self, cursor_data: Any = None, cursor_rowcount: int = 0):
        self.cursor_data = cursor_data
        self.cursor_rowcount = cursor_rowcount
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=True, buffered=True):
        """Mock create cursor"""
        return MockDatabaseCursor(self.cursor_data, self.cursor_rowcount)

    def commit(self):
        """Mock commit transaction"""
        self.committed = True

    def rollback(self):
        """Mock rollback transaction"""
        self.rolled_back = True

    def close(self):
        """Mock close connection"""
        pass


def create_mock_db_manager(return_data: Any = None, rowcount: int = 0):
    """Create a mock database manager"""
    mock_manager = Mock()
    mock_connection = MockDatabaseConnection(return_data, rowcount)

    mock_manager.get_connection.return_value = mock_connection
    mock_manager.get_cursor.return_value.__enter__.return_value = mock_connection.cursor()
    mock_manager.get_cursor.return_value.__exit__.return_value = None
    mock_manager.transaction.return_value.__enter__.return_value = mock_connection.cursor()
    mock_manager.transaction.return_value.__exit__.return_value = None

    return mock_manager


def generate_test_data_set(count: int, data_type: str = 'customer') -> list:
    """Generate a test data set"""
    data_generators = {
        'customer': lambda i: {
            'customer_id': i,
            'first_name': f'Customer{i}',
            'family_name': 'Test',
            'full_name': f'Customer{i} Test',
            'email': f'customer{i}@test.com',
            'phone': f'555{i:07d}',
            'address': f'{i} Test Street'
        },
        'job': lambda i: {
            'job_id': i,
            'customer_id': (i - 1) % 10 + 1,
            'vehicle_info': f'Test Vehicle {i}',
            'problem_description': f'Problem description {i}',
            'status': ['pending', 'in_progress', 'completed'][i % 3],
            'total_cost': 100.0 * i
        },
        'service': lambda i: {
            'service_id': i,
            'service_name': f'Service {i}',
            'description': f'Service description {i}',
            'base_price': 50.0 * i,
            'estimated_hours': i % 8 + 1
        },
        'part': lambda i: {
            'part_id': i,
            'part_name': f'Part {i}',
            'part_number': f'P{i:03d}',
            'price': 10.0 * i,
            'supplier': f'Supplier {i}',
            'stock_quantity': i * 10
        }
    }

    generator = data_generators.get(data_type)
    if not generator:
        raise ValueError(f"Unsupported data type: {data_type}")

    return [generator(i) for i in range(1, count + 1)]


class TestResponseHelper:
    """Test response assertion helper"""

    @staticmethod
    def assert_success_response(response, expected_message: str = None):
        """Assert successful response"""
        assert response.status_code == 200
        if expected_message:
            assert expected_message.encode('utf-8') in response.data

    @staticmethod
    def assert_error_response(response, expected_status: int = 400, expected_message: str = None):
        """Assert error response"""
        assert response.status_code == expected_status
        if expected_message:
            assert expected_message.encode('utf-8') in response.data

    @staticmethod
    def assert_api_success(response, expected_data_keys: list = None):
        """Assert API success response"""
        data = assert_json_response(response, 200)
        if expected_data_keys:
            for key in expected_data_keys:
                assert key in data
        return data

    @staticmethod
    def assert_api_error(response, expected_status: int = 400, expected_error_key: str = 'error'):
        """Assert API error response"""
        data = assert_json_response(response, expected_status)
        assert expected_error_key in data
        return data


def mock_security_decorators():
    """Mock security decorators to disable security checks in tests"""
    def csrf_protect_mock(f):
        return f

    def require_auth_mock(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    return csrf_protect_mock, require_auth_mock
