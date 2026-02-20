# Automotive Repair Management System - Test Framework

## Overview

This test framework provides comprehensive test coverage for the automotive repair management system, including unit tests, integration tests, and security tests. Uses pytest as the test runner with support for mocking, coverage checks, and CI.

## Test Structure

```
tests/
├── __init__.py                 # Test module initialization
├── conftest.py                 # pytest configuration and fixtures
├── utils.py                    # Test utilities and helpers
├── README.md                   # Test documentation
├── unit/                       # Unit tests
│   ├── test_basic.py          # Basic functionality tests
│   ├── test_security.py       # Security module tests
│   ├── test_models.py         # Model layer tests
│   └── test_multitenant.py    # Multi-tenant tests
├── integration/                # Integration tests
│   └── test_views.py          # View layer integration tests
└── fixtures/                   # Test data and fixtures
```

## Quick Start

### Install Dependencies

```bash
pip install pytest pytest-cov pytest-mock
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run security tests
pytest tests/ -m security -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow tests

## Test Types

### Unit Tests

Test individual modules, classes, or functions:

- **Security module tests** (`test_security.py`) - Password hashing, input sanitization, SQL injection prevention, CSRF protection, session security
- **Model layer tests** (`test_models.py`) - Model instantiation, business logic
- **Multi-tenant tests** (`test_multitenant.py`) - Permission system, tenant model, validators

### Integration Tests

Test module interactions and system functionality:

- **View layer tests** (`test_views.py`) - Route access, authentication, response codes, API endpoints

## Fixtures

Defined in `conftest.py`:

- `app` - Flask application instance
- `client` - Test client
- `sample_*_data` - Sample data fixtures
- `authenticated_session` - Authenticated technician session
- `admin_session` - Administrator session

## Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_security.py -v

# Run a specific test class
pytest tests/unit/test_security.py::TestPasswordSecurity -v

# Run a specific test method
pytest tests/unit/test_security.py::TestPasswordSecurity::test_hash_password_generates_different_hashes -v

# Show print output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -v -x
```
