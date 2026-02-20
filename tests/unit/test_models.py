"""
Model Unit Tests
Tests for Customer, Job, Service, Part model business logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date


@pytest.mark.unit
class TestCustomerModel:
    """Customer model tests"""

    def test_customer_creation(self, app):
        """Test customer model can be instantiated"""
        with app.app_context():
            from app.models.customer import Customer
            customer = Customer(
                first_name='John',
                family_name='Smith',
                email='john@example.com',
                phone='5551234567',
                tenant_id=1,
            )
            assert customer.first_name == 'John'
            assert customer.family_name == 'Smith'
            assert customer.email == 'john@example.com'

    def test_customer_full_name(self, app):
        """Test customer full_name property"""
        with app.app_context():
            from app.models.customer import Customer
            customer = Customer(
                first_name='John',
                family_name='Smith',
                tenant_id=1,
            )
            assert customer.full_name == 'John Smith'


@pytest.mark.unit
class TestServiceModel:
    """Service model tests"""

    def test_service_creation(self, app):
        """Test service model can be instantiated"""
        with app.app_context():
            from app.models.service import Service
            service = Service(
                service_name='Oil Change',
                cost=49.99,
                tenant_id=1,
                category='Maintenance',
                is_active=True,
            )
            assert service.service_name == 'Oil Change'
            assert service.cost == 49.99
            assert service.is_active is True


@pytest.mark.unit
class TestPartModel:
    """Part model tests"""

    def test_part_creation(self, app):
        """Test part model can be instantiated"""
        with app.app_context():
            from app.models.part import Part
            part = Part(
                part_name='Oil Filter',
                cost=12.99,
                sku='OIL-FLT-001',
                tenant_id=1,
                category='Filters',
                is_active=True,
            )
            assert part.part_name == 'Oil Filter'
            assert part.cost == 12.99
            assert part.sku == 'OIL-FLT-001'


@pytest.mark.unit
class TestTenantModel:
    """Tenant model tests"""

    def test_tenant_creation(self, app):
        """Test tenant model can be instantiated"""
        with app.app_context():
            from app.models.tenant import Tenant
            tenant = Tenant(
                name="Joe's Auto Repair",
                slug='joes-auto-repair',
                business_type='auto_repair',
                status='active',
            )
            assert tenant.name == "Joe's Auto Repair"
            assert tenant.slug == 'joes-auto-repair'
            assert tenant.business_type == 'auto_repair'


@pytest.mark.unit
class TestSubscriptionModel:
    """Subscription model tests"""

    def test_subscription_creation(self, app):
        """Test subscription model can be instantiated"""
        with app.app_context():
            from app.models.subscription import Subscription
            sub = Subscription(
                tenant_id=1,
                plan='starter',
                status='active',
            )
            assert sub.plan == 'starter'
            assert sub.status == 'active'
