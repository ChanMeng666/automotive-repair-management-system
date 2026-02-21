"""
Tenant Service
Business logic for tenant management, invitations, and onboarding
"""
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
import logging
from app.extensions import db
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.subscription import Subscription
from app.models.user import User


class TenantService:
    """Tenant lifecycle and membership management"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_tenant(
        self,
        name: str,
        owner_user_id: int,
        business_type: str = 'auto_repair',
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Tuple[bool, List[str], Optional[Tenant]]:
        """
        Create a new tenant with the given user as owner.

        Returns:
            (success, errors, tenant)
        """
        try:
            # Validate business type
            if business_type not in Tenant.VALID_TYPES:
                return False, [f"Invalid business type: {business_type}"], None

            owner = User.find_by_id(owner_user_id)
            if not owner:
                return False, ["User not found"], None

            # Prevent duplicate tenant name per user (case-insensitive)
            existing_owned = db.session.execute(
                db.select(TenantMembership)
                .join(Tenant, Tenant.tenant_id == TenantMembership.tenant_id)
                .where(
                    TenantMembership.user_id == owner_user_id,
                    TenantMembership.role == TenantMembership.ROLE_OWNER,
                    db.func.lower(Tenant.name) == name.strip().lower(),
                )
            ).scalar_one_or_none()

            if existing_owned:
                return False, ["You already own an organization with this name"], None

            slug = Tenant.generate_slug(name)

            tenant = Tenant(
                name=name,
                slug=slug,
                business_type=business_type,
                email=email or owner.email,
                phone=phone,
                address=address,
                status=Tenant.STATUS_TRIAL,
                trial_ends_at=datetime.utcnow() + timedelta(days=14),
                settings={
                    'currency': 'USD',
                    'tax_rate': 0.0,
                },
            )
            db.session.add(tenant)
            db.session.flush()  # get tenant_id

            # Create owner membership — only set is_default if user has no existing default
            has_default = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == owner_user_id,
                    TenantMembership.is_default == True,
                )
            ).scalar_one_or_none()

            membership = TenantMembership(
                user_id=owner_user_id,
                tenant_id=tenant.tenant_id,
                role=TenantMembership.ROLE_OWNER,
                is_default=(has_default is None),
                status=TenantMembership.STATUS_ACTIVE,
                accepted_at=datetime.utcnow(),
            )
            db.session.add(membership)

            # Create free subscription
            subscription = Subscription(
                tenant_id=tenant.tenant_id,
                plan=Subscription.PLAN_FREE,
                status=Subscription.STATUS_TRIALING,
                trial_ends_at=tenant.trial_ends_at,
            )
            db.session.add(subscription)

            db.session.commit()
            self.logger.info(f"Tenant created: {tenant.name} (slug={tenant.slug})")
            return True, [], tenant

        except Exception as e:
            self.logger.error(f"Failed to create tenant: {e}")
            db.session.rollback()
            return False, ["Failed to create organization"], None

    def invite_member(
        self,
        tenant_id: int,
        email: str,
        role: str,
        invited_by_user_id: int,
    ) -> Tuple[bool, List[str], Optional[TenantMembership]]:
        """
        Invite a user to a tenant by email.

        Returns:
            (success, errors, membership)
        """
        try:
            if role not in TenantMembership.VALID_ROLES:
                return False, [f"Invalid role: {role}"], None

            if role == TenantMembership.ROLE_OWNER:
                return False, ["Cannot invite as owner"], None

            tenant = Tenant.find_by_id(tenant_id)
            if not tenant:
                return False, ["Organization not found"], None

            # Find user by email
            user = User.find_by_email(email)
            if not user:
                return False, ["User not found. They must register first."], None

            # Check for existing membership
            existing = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user.user_id,
                    TenantMembership.tenant_id == tenant_id,
                )
            ).scalar_one_or_none()

            if existing:
                return False, ["User is already a member of this organization"], None

            membership = TenantMembership(
                user_id=user.user_id,
                tenant_id=tenant_id,
                role=role,
                invited_by=invited_by_user_id,
                invited_at=datetime.utcnow(),
                status=TenantMembership.STATUS_PENDING,
            )
            db.session.add(membership)
            db.session.commit()

            self.logger.info(
                f"Invited {email} to tenant {tenant.name} as {role}"
            )
            return True, [], membership

        except Exception as e:
            self.logger.error(f"Failed to invite member: {e}")
            db.session.rollback()
            return False, ["Failed to send invitation"], None

    def accept_invitation(
        self, membership_id: int, user_id: int
    ) -> Tuple[bool, List[str]]:
        """
        Accept a pending invitation.

        Returns:
            (success, errors)
        """
        try:
            membership = TenantMembership.find_by_id(membership_id)
            if not membership:
                return False, ["Invitation not found"]

            if membership.user_id != user_id:
                return False, ["This invitation is not for you"]

            if membership.status != TenantMembership.STATUS_PENDING:
                return False, ["This invitation has already been processed"]

            membership.status = TenantMembership.STATUS_ACTIVE
            membership.accepted_at = datetime.utcnow()

            # If user has no default tenant, make this the default
            has_default = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.is_default == True,
                )
            ).scalar_one_or_none()

            if not has_default:
                membership.is_default = True

            db.session.commit()
            self.logger.info(
                f"User {user_id} accepted invitation to tenant {membership.tenant_id}"
            )
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to accept invitation: {e}")
            db.session.rollback()
            return False, ["Failed to accept invitation"]

    def get_pending_invitations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all pending invitations for a user.

        Returns:
            List of dicts with membership_id, tenant_name, tenant_slug, role, invited_at, invited_by
        """
        try:
            pending = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == TenantMembership.STATUS_PENDING,
                )
            ).scalars().all()

            results = []
            for m in pending:
                tenant = Tenant.find_by_id(m.tenant_id)
                invited_by_user = User.find_by_id(m.invited_by) if m.invited_by else None
                if tenant:
                    results.append({
                        'membership_id': m.membership_id,
                        'tenant_name': tenant.name,
                        'tenant_slug': tenant.slug,
                        'role': m.role,
                        'invited_at': m.invited_at,
                        'invited_by': invited_by_user.username if invited_by_user else None,
                    })
            return results

        except Exception as e:
            self.logger.error(f"Failed to get pending invitations: {e}")
            return []

    def decline_invitation(
        self, membership_id: int, user_id: int
    ) -> Tuple[bool, List[str]]:
        """
        Decline a pending invitation by deleting the membership record.

        Returns:
            (success, errors)
        """
        try:
            membership = TenantMembership.find_by_id(membership_id)
            if not membership:
                return False, ["Invitation not found"]

            if membership.user_id != user_id:
                return False, ["This invitation is not for you"]

            if membership.status != TenantMembership.STATUS_PENDING:
                return False, ["This invitation has already been processed"]

            db.session.delete(membership)
            db.session.commit()
            self.logger.info(
                f"User {user_id} declined invitation to tenant {membership.tenant_id}"
            )
            return True, []

        except Exception as e:
            self.logger.error(f"Failed to decline invitation: {e}")
            db.session.rollback()
            return False, ["Failed to decline invitation"]

    def get_user_tenants(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all tenants a user belongs to"""
        try:
            memberships = db.session.execute(
                db.select(TenantMembership)
                .where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                )
                .order_by(TenantMembership.is_default.desc())
            ).scalars().all()

            results = []
            for m in memberships:
                tenant = Tenant.find_by_id(m.tenant_id)
                if tenant:
                    results.append({
                        'tenant_id': tenant.tenant_id,
                        'name': tenant.name,
                        'slug': tenant.slug,
                        'role': m.role,
                        'is_default': m.is_default,
                        'status': tenant.status,
                    })
            return results

        except Exception as e:
            self.logger.error(f"Failed to get user tenants: {e}")
            return []

    def get_default_tenant_id(self, user_id: int) -> Optional[int]:
        """Get user's default tenant ID"""
        try:
            membership = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                    TenantMembership.is_default == True,
                )
            ).scalar_one_or_none()

            if membership:
                return membership.tenant_id

            # Fall back to first active membership
            membership = db.session.execute(
                db.select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == TenantMembership.STATUS_ACTIVE,
                ).order_by(TenantMembership.created_at)
            ).scalars().first()

            return membership.tenant_id if membership else None

        except Exception as e:
            self.logger.error(f"Failed to get default tenant: {e}")
            return None
