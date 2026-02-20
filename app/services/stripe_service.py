"""
Stripe Service
Handles Stripe billing integration for SaaS subscriptions
"""
from typing import Optional, Dict, Any, Tuple, List
import logging
from flask import current_app
from app.extensions import db
from app.models.subscription import Subscription
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# Plan configuration
PLAN_CONFIG = {
    'free': {
        'name': 'Free',
        'price_monthly': 0,
        'max_users': 2,
        'max_jobs_per_month': 20,
    },
    'starter': {
        'name': 'Starter',
        'price_monthly': 29,
        'max_users': 5,
        'max_jobs_per_month': 100,
    },
    'professional': {
        'name': 'Professional',
        'price_monthly': 79,
        'max_users': 20,
        'max_jobs_per_month': -1,  # unlimited
    },
    'enterprise': {
        'name': 'Enterprise',
        'price_monthly': 199,
        'max_users': -1,  # unlimited
        'max_jobs_per_month': -1,
    },
}


def _get_stripe():
    """Lazy-import stripe to avoid issues when not installed"""
    import stripe
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    return stripe


class StripeService:
    """Stripe billing operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_stripe_customer(self, tenant: Tenant) -> Optional[str]:
        """
        Create a Stripe customer for a tenant.

        Returns:
            Stripe customer ID or None on failure
        """
        try:
            stripe = _get_stripe()
            customer = stripe.Customer.create(
                name=tenant.name,
                email=tenant.email,
                metadata={
                    'tenant_id': str(tenant.tenant_id),
                    'slug': tenant.slug,
                },
            )

            # Store the Stripe customer ID
            sub = db.session.execute(
                db.select(Subscription).where(
                    Subscription.tenant_id == tenant.tenant_id
                )
            ).scalar_one_or_none()

            if sub:
                sub.stripe_customer_id = customer.id
                db.session.commit()

            self.logger.info(
                f"Created Stripe customer {customer.id} for tenant {tenant.slug}"
            )
            return customer.id

        except Exception as e:
            self.logger.error(f"Failed to create Stripe customer: {e}")
            return None

    def create_subscription(
        self, tenant_id: int, price_id: str
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Create a Stripe subscription for a tenant.

        Returns:
            (success, errors, stripe_subscription_id)
        """
        try:
            stripe = _get_stripe()
            sub = db.session.execute(
                db.select(Subscription).where(
                    Subscription.tenant_id == tenant_id
                )
            ).scalar_one_or_none()

            if not sub:
                return False, ["No subscription record found"], None

            if not sub.stripe_customer_id:
                tenant = Tenant.find_by_id(tenant_id)
                if not tenant:
                    return False, ["Tenant not found"], None
                customer_id = self.create_stripe_customer(tenant)
                if not customer_id:
                    return False, ["Failed to create Stripe customer"], None
                sub.stripe_customer_id = customer_id

            stripe_sub = stripe.Subscription.create(
                customer=sub.stripe_customer_id,
                items=[{'price': price_id}],
                trial_from_plan=True,
                metadata={'tenant_id': str(tenant_id)},
            )

            sub.stripe_subscription_id = stripe_sub.id
            sub.status = Subscription.STATUS_ACTIVE
            if stripe_sub.current_period_start:
                from datetime import datetime
                sub.current_period_start = datetime.utcfromtimestamp(
                    stripe_sub.current_period_start
                )
            if stripe_sub.current_period_end:
                sub.current_period_end = datetime.utcfromtimestamp(
                    stripe_sub.current_period_end
                )

            db.session.commit()
            self.logger.info(
                f"Created Stripe subscription {stripe_sub.id} for tenant {tenant_id}"
            )
            return True, [], stripe_sub.id

        except Exception as e:
            self.logger.error(f"Failed to create subscription: {e}")
            db.session.rollback()
            return False, ["Failed to create subscription"], None

    def handle_webhook(self, payload: bytes, sig_header: str) -> Tuple[bool, str]:
        """
        Process a Stripe webhook event.

        Returns:
            (success, message)
        """
        try:
            stripe = _get_stripe()
            webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )

            event_type = event['type']
            data = event['data']['object']

            if event_type == 'customer.subscription.updated':
                self._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                self._handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_failed':
                self._handle_payment_failed(data)
            elif event_type == 'invoice.paid':
                self._handle_invoice_paid(data)

            return True, f"Handled {event_type}"

        except ValueError:
            return False, "Invalid payload"
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return False, str(e)

    def _handle_subscription_updated(self, data: dict) -> None:
        """Handle subscription update event"""
        stripe_sub_id = data.get('id')
        sub = db.session.execute(
            db.select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        ).scalar_one_or_none()

        if sub:
            status = data.get('status')
            status_map = {
                'trialing': Subscription.STATUS_TRIALING,
                'active': Subscription.STATUS_ACTIVE,
                'past_due': Subscription.STATUS_PAST_DUE,
                'canceled': Subscription.STATUS_CANCELED,
            }
            if status in status_map:
                sub.status = status_map[status]

            from datetime import datetime
            if data.get('current_period_start'):
                sub.current_period_start = datetime.utcfromtimestamp(
                    data['current_period_start']
                )
            if data.get('current_period_end'):
                sub.current_period_end = datetime.utcfromtimestamp(
                    data['current_period_end']
                )
            db.session.commit()

    def _handle_subscription_deleted(self, data: dict) -> None:
        """Handle subscription cancellation"""
        stripe_sub_id = data.get('id')
        sub = db.session.execute(
            db.select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        ).scalar_one_or_none()

        if sub:
            sub.status = Subscription.STATUS_CANCELED
            db.session.commit()

    def _handle_payment_failed(self, data: dict) -> None:
        """Handle failed payment"""
        customer_id = data.get('customer')
        sub = db.session.execute(
            db.select(Subscription).where(
                Subscription.stripe_customer_id == customer_id
            )
        ).scalar_one_or_none()

        if sub:
            sub.status = Subscription.STATUS_PAST_DUE
            db.session.commit()

    def _handle_invoice_paid(self, data: dict) -> None:
        """Handle successful payment"""
        customer_id = data.get('customer')
        sub = db.session.execute(
            db.select(Subscription).where(
                Subscription.stripe_customer_id == customer_id
            )
        ).scalar_one_or_none()

        if sub and sub.status == Subscription.STATUS_PAST_DUE:
            sub.status = Subscription.STATUS_ACTIVE
            db.session.commit()

    def create_checkout_session(
        self, tenant_id: int, price_id: str, success_url: str, cancel_url: str
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Create a Stripe Checkout session for plan upgrade.

        Returns:
            (success, errors, checkout_url)
        """
        try:
            stripe = _get_stripe()
            sub = db.session.execute(
                db.select(Subscription).where(
                    Subscription.tenant_id == tenant_id
                )
            ).scalar_one_or_none()

            if not sub:
                return False, ["No subscription record found"], None

            if not sub.stripe_customer_id:
                tenant = Tenant.find_by_id(tenant_id)
                if not tenant:
                    return False, ["Tenant not found"], None
                customer_id = self.create_stripe_customer(tenant)
                if not customer_id:
                    return False, ["Failed to create Stripe customer"], None
                sub.stripe_customer_id = customer_id
                db.session.commit()

            session = stripe.checkout.Session.create(
                customer=sub.stripe_customer_id,
                mode='subscription',
                line_items=[{'price': price_id, 'quantity': 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'tenant_id': str(tenant_id)},
            )

            return True, [], session.url

        except Exception as e:
            self.logger.error(f"Failed to create checkout session: {e}")
            return False, ["Failed to start checkout"], None

    def create_billing_portal_session(
        self, tenant_id: int, return_url: str
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Create a Stripe Billing Portal session.

        Returns:
            (success, errors, portal_url)
        """
        try:
            stripe = _get_stripe()
            sub = db.session.execute(
                db.select(Subscription).where(
                    Subscription.tenant_id == tenant_id
                )
            ).scalar_one_or_none()

            if not sub or not sub.stripe_customer_id:
                return False, ["No billing account found"], None

            session = stripe.billing_portal.Session.create(
                customer=sub.stripe_customer_id,
                return_url=return_url,
            )

            return True, [], session.url

        except Exception as e:
            self.logger.error(f"Failed to create billing portal: {e}")
            return False, ["Failed to open billing portal"], None

    def get_subscription_status(self, tenant_id: int) -> Dict[str, Any]:
        """Get current subscription status for a tenant"""
        try:
            sub = db.session.execute(
                db.select(Subscription).where(
                    Subscription.tenant_id == tenant_id
                )
            ).scalar_one_or_none()

            if not sub:
                return {'plan': 'free', 'status': 'none'}

            plan_info = PLAN_CONFIG.get(sub.plan, PLAN_CONFIG['free'])

            return {
                'plan': sub.plan,
                'plan_name': plan_info['name'],
                'status': sub.status,
                'is_active': sub.is_active,
                'max_users': plan_info['max_users'],
                'max_jobs_per_month': plan_info['max_jobs_per_month'],
                'current_period_end': (
                    sub.current_period_end.isoformat()
                    if sub.current_period_end
                    else None
                ),
                'trial_ends_at': (
                    sub.trial_ends_at.isoformat()
                    if sub.trial_ends_at
                    else None
                ),
            }

        except Exception as e:
            self.logger.error(f"Failed to get subscription status: {e}")
            return {'plan': 'free', 'status': 'error'}
