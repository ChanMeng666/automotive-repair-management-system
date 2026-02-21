"""
SaaS Billing Blueprint
Handles subscription plans, Stripe checkout, billing portal, and webhooks
"""
import logging
from flask import Blueprint, request, redirect, url_for, render_template, flash, g, jsonify
from app.utils.decorators import login_required
from app.services.stripe_service import StripeService, PLAN_CONFIG
from app.extensions import db

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')
logger = logging.getLogger(__name__)
stripe_service = StripeService()


@billing_bp.route('/plans')
@login_required
def plans():
    """Show available subscription plans"""
    tenant_id = getattr(g, 'current_tenant_id', None)
    current_plan = {}
    if tenant_id:
        current_plan = stripe_service.get_subscription_status(tenant_id)

    return render_template(
        'billing/plans.html',
        plans=PLAN_CONFIG,
        current_plan=current_plan,
    )


@billing_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Create a Stripe Checkout session and redirect"""
    tenant_id = getattr(g, 'current_tenant_id', None)
    if not tenant_id:
        flash('No organization selected.', 'error')
        return redirect(url_for('billing.plans'))

    price_id = request.form.get('price_id')
    if not price_id:
        flash('Please select a plan.', 'error')
        return redirect(url_for('billing.plans'))

    success_url = url_for('billing.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = url_for('billing.plans', _external=True)

    ok, errors, checkout_url = stripe_service.create_checkout_session(
        tenant_id, price_id, success_url, cancel_url
    )

    if ok and checkout_url:
        return redirect(checkout_url)

    for err in errors:
        flash(err, 'error')
    return redirect(url_for('billing.plans'))


@billing_bp.route('/success')
@login_required
def success():
    """Checkout success page"""
    return render_template('billing/success.html')


@billing_bp.route('/portal', methods=['POST'])
@login_required
def portal():
    """Redirect to Stripe Billing Portal"""
    tenant_id = getattr(g, 'current_tenant_id', None)
    if not tenant_id:
        flash('No organization selected.', 'error')
        return redirect(url_for('billing.plans'))

    return_url = url_for('billing.plans', _external=True)

    ok, errors, portal_url = stripe_service.create_billing_portal_session(
        tenant_id, return_url
    )

    if ok and portal_url:
        return redirect(portal_url)

    for err in errors:
        flash(err, 'error')
    return redirect(url_for('billing.plans'))


@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events (no auth required)"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')

    ok, message = stripe_service.handle_webhook(payload, sig_header)

    if ok:
        return jsonify({'status': 'ok'}), 200
    else:
        logger.warning(f"Webhook failed: {message}")
        return jsonify({'error': message}), 400
