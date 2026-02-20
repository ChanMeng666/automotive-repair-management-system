"""
Onboarding Routes Blueprint
Multi-step wizard for setting up a new organization
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import logging
from app.utils.decorators import handle_database_errors
from app.utils.validators import sanitize_input

onboarding_bp = Blueprint('onboarding', __name__)
logger = logging.getLogger(__name__)


def require_login_and_tenant():
    """Ensure user is logged in and has a tenant context"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('main.login'))
    if not session.get('current_tenant_id'):
        flash('Please select or create an organization first', 'warning')
        return redirect(url_for('auth.select_tenant'))
    return None


@onboarding_bp.route('/step/<int:step_number>')
@handle_database_errors
def step(step_number):
    """Display onboarding step"""
    redirect_response = require_login_and_tenant()
    if redirect_response:
        return redirect_response

    if step_number < 1 or step_number > 4:
        return redirect(url_for('onboarding.step', step_number=1))

    tenant_id = session.get('current_tenant_id')
    tenant_name = session.get('current_tenant_name', '')

    template_map = {
        1: 'onboarding/step1.html',
        2: 'onboarding/step2.html',
        3: 'onboarding/step3.html',
        4: 'onboarding/step4.html',
    }

    context = {
        'step_number': step_number,
        'total_steps': 4,
        'tenant_name': tenant_name,
    }

    # Load step-specific data
    if step_number == 2:
        from app.models.service import Service
        from flask import g
        g.current_tenant_id = tenant_id
        context['services'] = Service.get_all_sorted()

    elif step_number == 3:
        from app.models.part import Part
        from flask import g
        g.current_tenant_id = tenant_id
        context['parts'] = Part.get_all_sorted()

    return render_template(template_map[step_number], **context)


@onboarding_bp.route('/step/<int:step_number>', methods=['POST'])
@handle_database_errors
def save_step(step_number):
    """Save onboarding step data"""
    redirect_response = require_login_and_tenant()
    if redirect_response:
        return redirect_response

    tenant_id = session.get('current_tenant_id')

    try:
        if step_number == 1:
            _save_step1(tenant_id)
        elif step_number == 2:
            _save_step2(tenant_id)
        elif step_number == 3:
            _save_step3(tenant_id)
        elif step_number == 4:
            _save_step4(tenant_id)
            flash('Setup complete! Welcome to AutoRepair Pro.', 'success')
            return redirect(url_for('onboarding.complete'))

        # Move to next step
        next_step = min(step_number + 1, 4)
        return redirect(url_for('onboarding.step', step_number=next_step))

    except Exception as e:
        logger.error(f"Onboarding step {step_number} save failed: {e}")
        flash('Failed to save settings. Please try again.', 'error')
        return redirect(url_for('onboarding.step', step_number=step_number))


@onboarding_bp.route('/complete')
@handle_database_errors
def complete():
    """Onboarding completion page"""
    redirect_response = require_login_and_tenant()
    if redirect_response:
        return redirect_response

    tenant_name = session.get('current_tenant_name', 'Your Organization')
    tenant_slug = session.get('current_tenant_slug', '')

    return render_template('onboarding/complete.html',
                         tenant_name=tenant_name,
                         tenant_slug=tenant_slug)


def _save_step1(tenant_id):
    """Save business details (step 1)"""
    from app.models.tenant import Tenant
    from app.extensions import db

    tenant = Tenant.find_by_id(tenant_id)
    if not tenant:
        raise ValueError("Organization not found")

    tenant.name = sanitize_input(request.form.get('name', tenant.name))
    tenant.email = sanitize_input(request.form.get('email', '')) or tenant.email
    tenant.phone = sanitize_input(request.form.get('phone', '')) or tenant.phone
    tenant.address = sanitize_input(request.form.get('address', '')) or tenant.address
    tenant.business_type = sanitize_input(request.form.get('business_type', tenant.business_type))

    # Update settings
    settings = tenant.settings or {}
    tax_rate = request.form.get('tax_rate')
    if tax_rate:
        try:
            settings['tax_rate'] = float(tax_rate)
        except ValueError:
            pass
    settings['currency'] = sanitize_input(request.form.get('currency', 'USD'))
    tenant.settings = settings

    # Update session with potentially new name
    session['current_tenant_name'] = tenant.name

    db.session.commit()


def _save_step2(tenant_id):
    """Save service catalog (step 2) - services are already seeded, this is for modifications"""
    from app.models.service import Service
    from app.extensions import db
    from flask import g

    g.current_tenant_id = tenant_id

    # Handle adding custom services
    service_name = sanitize_input(request.form.get('service_name', ''))
    cost = request.form.get('cost')
    category = sanitize_input(request.form.get('category', ''))

    if service_name and cost:
        try:
            service = Service(
                tenant_id=tenant_id,
                service_name=service_name,
                cost=float(cost),
                category=category or 'General',
                is_active=True,
            )
            db.session.add(service)
            db.session.commit()
            flash(f'Service "{service_name}" added!', 'success')
        except (ValueError, Exception) as e:
            logger.error(f"Failed to add service during onboarding: {e}")
            db.session.rollback()


def _save_step3(tenant_id):
    """Save parts catalog (step 3) - parts are already seeded, this is for modifications"""
    from app.models.part import Part
    from app.extensions import db
    from flask import g

    g.current_tenant_id = tenant_id

    # Handle adding custom parts
    part_name = sanitize_input(request.form.get('part_name', ''))
    cost = request.form.get('cost')
    sku = sanitize_input(request.form.get('sku', ''))
    category = sanitize_input(request.form.get('category', ''))

    if part_name and cost:
        try:
            part = Part(
                tenant_id=tenant_id,
                part_name=part_name,
                cost=float(cost),
                sku=sku or None,
                category=category or 'General',
                is_active=True,
            )
            db.session.add(part)
            db.session.commit()
            flash(f'Part "{part_name}" added!', 'success')
        except (ValueError, Exception) as e:
            logger.error(f"Failed to add part during onboarding: {e}")
            db.session.rollback()


def _save_step4(tenant_id):
    """Save team invitations (step 4)"""
    from app.services.tenant_service import TenantService

    tenant_service = TenantService()
    user_id = session.get('user_id')

    # Process multiple invitation entries
    emails = request.form.getlist('invite_email')
    roles = request.form.getlist('invite_role')

    for email, role in zip(emails, roles):
        email = sanitize_input(email).strip()
        role = sanitize_input(role).strip()

        if email and role:
            success, errors, _ = tenant_service.invite_member(
                tenant_id=tenant_id,
                email=email,
                role=role,
                invited_by_user_id=user_id,
            )
            if success:
                flash(f'Invitation sent to {email}', 'success')
            else:
                for error in errors:
                    flash(f'{email}: {error}', 'warning')
