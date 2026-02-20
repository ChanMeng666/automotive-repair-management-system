"""
User Model - SQLAlchemy ORM
Authentication and authorization with multi-tenant support
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import BaseModelMixin, TimestampMixin

# Role-permission mapping for the multi-tenant RBAC system
ROLE_PERMISSIONS = {
    'owner': [
        'manage_org', 'manage_users', 'manage_catalog', 'manage_inventory',
        'manage_jobs', 'manage_customers', 'manage_billing', 'view_reports'
    ],
    'admin': [
        'manage_users', 'manage_catalog', 'manage_inventory',
        'manage_jobs', 'manage_customers', 'manage_billing', 'view_reports'
    ],
    'manager': ['manage_jobs', 'manage_customers', 'manage_billing', 'view_reports'],
    'technician': ['manage_jobs', 'view_reports'],
    'parts_clerk': ['manage_catalog', 'manage_inventory', 'view_reports'],
    'viewer': ['view_reports'],
}

VALID_ROLES = list(ROLE_PERMISSIONS.keys())


class User(db.Model, BaseModelMixin, TimestampMixin):
    """User model for authentication"""

    __tablename__ = 'user'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Legacy role column kept for backward compatibility during migration
    role: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # Neon Auth integration fields
    neon_auth_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)

    # Relationships
    memberships: Mapped[List["TenantMembership"]] = relationship(
        "TenantMembership",
        back_populates="user",
        foreign_keys="TenantMembership.user_id",
        lazy="dynamic"
    )

    @property
    def is_admin(self) -> bool:
        """Check if user is a superadmin or has admin/owner role in any tenant"""
        if self.is_superadmin:
            return True
        # Legacy support
        if self.role == 'administrator':
            return True
        return False

    @property
    def is_technician(self) -> bool:
        """Check if user has technician role (legacy support)"""
        return self.role == 'technician'

    def get_tenants(self) -> List[Dict[str, Any]]:
        """Get all tenants this user belongs to"""
        from app.models.tenant_membership import TenantMembership
        memberships = db.session.execute(
            db.select(TenantMembership).where(
                db.and_(
                    TenantMembership.user_id == self.user_id,
                    TenantMembership.status == 'active'
                )
            )
        ).scalars().all()
        result = []
        for m in memberships:
            result.append({
                'tenant_id': m.tenant_id,
                'tenant_name': m.tenant.name if m.tenant else None,
                'tenant_slug': m.tenant.slug if m.tenant else None,
                'role': m.role,
                'is_default': m.is_default,
            })
        return result

    def get_role_in_tenant(self, tenant_id: int) -> Optional[str]:
        """Get user's role in a specific tenant"""
        if self.is_superadmin:
            return 'owner'
        from app.models.tenant_membership import TenantMembership
        membership = db.session.execute(
            db.select(TenantMembership).where(
                db.and_(
                    TenantMembership.user_id == self.user_id,
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.status == 'active'
                )
            )
        ).scalar_one_or_none()
        return membership.role if membership else None

    def has_permission(self, tenant_id: int, permission: str) -> bool:
        """Check if user has a specific permission in a tenant"""
        if self.is_superadmin:
            return True
        role = self.get_role_in_tenant(tenant_id)
        if not role:
            return False
        return permission in ROLE_PERMISSIONS.get(role, [])

    def get_default_tenant_id(self) -> Optional[int]:
        """Get the user's default tenant ID"""
        from app.models.tenant_membership import TenantMembership
        # First try to find a default membership
        membership = db.session.execute(
            db.select(TenantMembership).where(
                db.and_(
                    TenantMembership.user_id == self.user_id,
                    TenantMembership.status == 'active',
                    TenantMembership.is_default == True
                )
            )
        ).scalar_one_or_none()
        if membership:
            return membership.tenant_id
        # Otherwise return the first active membership
        membership = db.session.execute(
            db.select(TenantMembership).where(
                db.and_(
                    TenantMembership.user_id == self.user_id,
                    TenantMembership.status == 'active'
                )
            ).order_by(TenantMembership.id)
        ).scalars().first()
        return membership.tenant_id if membership else None

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str) -> None:
        """Set a new password (hashed)"""
        self.password_hash = generate_password_hash(password)

    @classmethod
    def find_by_username(cls, username: str) -> Optional['User']:
        """Find user by username"""
        query = db.select(cls).where(cls.username == username)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email"""
        query = db.select(cls).where(cls.email == email)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def find_by_neon_auth_id(cls, neon_auth_user_id: str) -> Optional['User']:
        """Find user by Neon Auth user ID"""
        query = db.select(cls).where(cls.neon_auth_user_id == neon_auth_user_id)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password"""
        user = cls.find_by_username(username)
        if user and user.is_active and user.check_password(password):
            user.update_last_login()
            return user
        return None

    @classmethod
    def authenticate_with_jwt(cls, jwt_payload: dict) -> Optional['User']:
        """Authenticate user with Neon Auth JWT payload"""
        neon_auth_user_id = jwt_payload.get('sub')
        if not neon_auth_user_id:
            return None

        user = cls.find_by_neon_auth_id(neon_auth_user_id)
        if user:
            if user.is_active:
                user.update_last_login()
                return user
            return None

        email = jwt_payload.get('email')
        name = jwt_payload.get('name', '')

        if email:
            existing = cls.find_by_email(email)
            if existing:
                existing.neon_auth_user_id = neon_auth_user_id
                existing.update_last_login()
                db.session.commit()
                return existing

        username = email.split('@')[0] if email else f"user_{neon_auth_user_id[:8]}"
        base_username = username
        counter = 1
        while cls.find_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        user = cls(
            username=username,
            email=email,
            password_hash=generate_password_hash(__import__('secrets').token_urlsafe(32)),
            is_active=True,
            neon_auth_user_id=neon_auth_user_id,
        )
        db.session.add(user)
        db.session.commit()
        user.update_last_login()
        return user

    def update_last_login(self) -> bool:
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
        return True

    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional['User']:
        """Create a new user"""
        if cls.find_by_username(username):
            raise ValueError("Username already exists")
        if email and cls.find_by_email(email):
            raise ValueError("Email already registered")

        user = cls(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            role=role,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user

    def update_password(self, new_password: str) -> bool:
        """Update user's password"""
        self.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True

    def deactivate(self) -> bool:
        """Deactivate user account"""
        self.is_active = False
        db.session.commit()
        return True

    def activate(self) -> bool:
        """Activate user account"""
        self.is_active = True
        db.session.commit()
        return True

    @classmethod
    def get_by_role(cls, role: str) -> List['User']:
        """Get all users with a specific legacy role"""
        query = db.select(cls).where(db.and_(cls.role == role, cls.is_active == True))
        return list(db.session.execute(query).scalars())

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'is_superadmin': self.is_superadmin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive:
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
            data['neon_auth_user_id'] = self.neon_auth_user_id

        return data

    def __repr__(self) -> str:
        return f"<User {self.username}>"
