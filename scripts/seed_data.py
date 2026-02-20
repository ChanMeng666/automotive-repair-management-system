"""
Seed Data Script
Creates demo data for development and testing.
Usage: python scripts/seed_data.py

Set SEED_ADMIN_PASSWORD and SEED_TECH_PASSWORD environment variables
to specify custom passwords. Random passwords are generated if not set.
"""
import sys
import os
import secrets

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.subscription import Subscription
from app.models.customer import Customer
from app.models.job import Job
from app.models.service import Service
from app.models.part import Part
from app.models.inventory import Inventory


def seed():
    """Create demo data"""
    app = create_app('development')

    with app.app_context():
        print("Seeding demo data...")

        # Check if demo tenant already exists
        existing = Tenant.find_by_slug('joes-auto-repair')
        if existing:
            print("Demo data already exists. Skipping.")
            return

        # --- Users ---
        admin_password = os.environ.get('SEED_ADMIN_PASSWORD') or secrets.token_urlsafe(16)
        tech_password = os.environ.get('SEED_TECH_PASSWORD') or secrets.token_urlsafe(16)

        admin_user = User(
            username='admin',
            email='admin@demo.local',
            is_superadmin=False,
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)

        tech_user = User(
            username='tech1',
            email='tech1@demo.local',
        )
        tech_user.set_password(tech_password)
        db.session.add(tech_user)

        tech2_user = User(
            username='tech2',
            email='tech2@demo.local',
        )
        tech2_user.set_password(tech_password)
        db.session.add(tech2_user)

        db.session.flush()
        print(f"  Created users: admin (ID={admin_user.user_id}), tech1, tech2")

        # --- Tenant ---
        tenant = Tenant(
            name="Joe's Auto Repair",
            slug='joes-auto-repair',
            business_type='auto_repair',
            email='info@joesauto.local',
            phone='555-0100',
            address='123 Main Street, Springfield',
            status='active',
            settings={'currency': 'USD', 'tax_rate': 8.5},
        )
        db.session.add(tenant)
        db.session.flush()
        print(f"  Created tenant: {tenant.name} (ID={tenant.tenant_id})")

        # --- Memberships ---
        db.session.add(TenantMembership(
            user_id=admin_user.user_id,
            tenant_id=tenant.tenant_id,
            role='owner',
            is_default=True,
            status='active',
            accepted_at=datetime.utcnow(),
        ))
        db.session.add(TenantMembership(
            user_id=tech_user.user_id,
            tenant_id=tenant.tenant_id,
            role='technician',
            is_default=True,
            status='active',
            accepted_at=datetime.utcnow(),
        ))
        db.session.add(TenantMembership(
            user_id=tech2_user.user_id,
            tenant_id=tenant.tenant_id,
            role='technician',
            is_default=True,
            status='active',
            accepted_at=datetime.utcnow(),
        ))

        # --- Subscription ---
        db.session.add(Subscription(
            tenant_id=tenant.tenant_id,
            plan='starter',
            status='active',
        ))

        # --- Services ---
        services_data = [
            ('Oil Change', 49.99, 'Maintenance', 30),
            ('Brake Inspection', 29.99, 'Inspection', 20),
            ('Tire Rotation', 39.99, 'Maintenance', 25),
            ('Engine Diagnostic', 89.99, 'Diagnostic', 45),
            ('Battery Replacement', 149.99, 'Repair', 30),
            ('Wheel Alignment', 79.99, 'Maintenance', 40),
            ('Transmission Fluid Change', 129.99, 'Maintenance', 45),
            ('Air Filter Replacement', 24.99, 'Maintenance', 15),
            ('Coolant Flush', 69.99, 'Maintenance', 35),
            ('Spark Plug Replacement', 119.99, 'Repair', 40),
        ]
        services = []
        for name, cost, category, duration in services_data:
            s = Service(
                tenant_id=tenant.tenant_id,
                service_name=name,
                cost=cost,
                category=category,
                estimated_duration_minutes=duration,
                is_active=True,
            )
            db.session.add(s)
            services.append(s)
        db.session.flush()
        print(f"  Created {len(services)} services")

        # --- Parts ---
        parts_data = [
            ('Oil Filter', 12.99, 'OIL-FLT-001', 'Filters', 'AutoZone'),
            ('Brake Pads (Front)', 45.99, 'BRK-PAD-F01', 'Brakes', 'Bosch'),
            ('Brake Pads (Rear)', 39.99, 'BRK-PAD-R01', 'Brakes', 'Bosch'),
            ('Air Filter', 18.99, 'AIR-FLT-001', 'Filters', 'K&N'),
            ('Spark Plug', 8.99, 'SPK-PLG-001', 'Ignition', 'NGK'),
            ('Wiper Blade', 14.99, 'WPR-BLD-001', 'Exterior', 'Bosch'),
            ('Battery (Standard)', 129.99, 'BAT-STD-001', 'Electrical', 'Interstate'),
            ('Coolant (1 Gallon)', 19.99, 'CLT-GAL-001', 'Fluids', 'Prestone'),
            ('Transmission Fluid', 24.99, 'TRN-FLD-001', 'Fluids', 'Valvoline'),
            ('Cabin Air Filter', 16.99, 'CAB-FLT-001', 'Filters', 'Fram'),
        ]
        parts = []
        for name, cost, sku, category, supplier in parts_data:
            p = Part(
                tenant_id=tenant.tenant_id,
                part_name=name,
                cost=cost,
                sku=sku,
                category=category,
                supplier=supplier,
                is_active=True,
            )
            db.session.add(p)
            parts.append(p)
        db.session.flush()
        print(f"  Created {len(parts)} parts")

        # --- Customers ---
        customers_data = [
            ('John', 'Smith', 'john.smith@email.com', '555-0101'),
            ('Jane', 'Doe', 'jane.doe@email.com', '555-0102'),
            ('Robert', 'Johnson', 'r.johnson@email.com', '555-0103'),
            ('Emily', 'Williams', 'e.williams@email.com', '555-0104'),
            ('Michael', 'Brown', 'm.brown@email.com', '555-0105'),
            ('Sarah', 'Davis', 's.davis@email.com', '555-0106'),
            ('David', 'Miller', 'd.miller@email.com', '555-0107'),
            ('Lisa', 'Wilson', 'l.wilson@email.com', '555-0108'),
        ]
        customers = []
        for first, last, email, phone in customers_data:
            c = Customer(
                tenant_id=tenant.tenant_id,
                first_name=first,
                family_name=last,
                email=email,
                phone=phone,
            )
            db.session.add(c)
            customers.append(c)
        db.session.flush()
        print(f"  Created {len(customers)} customers")

        # --- Jobs ---
        today = date.today()
        jobs_data = [
            # (customer_index, days_ago, completed, paid)
            (0, 30, True, True),
            (0, 15, True, False),   # completed but unpaid
            (1, 20, True, True),
            (1, 5, False, False),   # in progress
            (2, 25, True, True),
            (2, 10, True, False),   # completed but unpaid (overdue)
            (3, 3, False, False),   # in progress
            (4, 45, True, True),
            (5, 1, False, False),   # new job today-ish
            (6, 60, True, True),
        ]
        for cust_idx, days_ago, completed, paid in jobs_data:
            j = Job(
                tenant_id=tenant.tenant_id,
                customer_id=customers[cust_idx].customer_id,
                job_date=today - timedelta(days=days_ago),
                completed=completed,
                paid=paid,
            )
            db.session.add(j)
        db.session.flush()
        print(f"  Created {len(jobs_data)} jobs")

        # --- Inventory ---
        for i, part in enumerate(parts):
            inv = Inventory(
                tenant_id=tenant.tenant_id,
                part_id=part.part_id,
                quantity_on_hand=20 + (i * 5),
                reorder_level=10,
                reorder_quantity=25,
                location=f'Shelf {chr(65 + i)}',
            )
            db.session.add(inv)
        db.session.flush()
        print(f"  Created {len(parts)} inventory records")

        db.session.commit()
        print("\nSeed data created successfully!")
        print(f"  Login: admin / {admin_password} (owner)")
        print(f"  Login: tech1 / {tech_password} (technician)")
        print(f"  Login: tech2 / {tech_password} (technician)")
        print(f"  Org: Joe's Auto Repair (slug: joes-auto-repair)")


if __name__ == '__main__':
    seed()
