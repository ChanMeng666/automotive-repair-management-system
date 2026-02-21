"""
Onboarding Routes Blueprint
Multi-step wizard for setting up a new organization (3 steps):
  Step 1: Configure Services
  Step 2: Add Parts & Inventory
  Step 3: Invite Team Members
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g
import logging
from app.extensions import db
from app.utils.decorators import handle_database_errors
from app.utils.validators import sanitize_input

onboarding_bp = Blueprint('onboarding', __name__)
logger = logging.getLogger(__name__)


def require_login_and_tenant():
    """Ensure user is logged in and has a tenant context"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('auth.login'))
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

    if step_number < 1 or step_number > 3:
        return redirect(url_for('onboarding.step', step_number=1))

    tenant_id = session.get('current_tenant_id')
    tenant_name = session.get('current_tenant_name', '')

    template_map = {
        1: 'onboarding/step_services.html',
        2: 'onboarding/step_parts.html',
        3: 'onboarding/step_team.html',
    }

    context = {
        'step_number': step_number,
        'total_steps': 3,
        'tenant_name': tenant_name,
    }

    # Load step-specific data
    if step_number == 1:
        from app.models.service import Service
        g.current_tenant_id = tenant_id
        context['services'] = Service.get_all_sorted()

    elif step_number == 2:
        from app.models.part import Part
        g.current_tenant_id = tenant_id
        context['parts'] = Part.get_all_sorted()

    elif step_number == 3:
        # Load pending invitations for this tenant
        from app.models.tenant_membership import TenantMembership
        from app.models.user import User
        g.current_tenant_id = tenant_id
        pending = db.session.execute(
            db.select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.status == TenantMembership.STATUS_PENDING,
            )
        ).scalars().all()
        invites = []
        for m in pending:
            user = User.find_by_id(m.user_id)
            invites.append({
                'email': user.email if user else 'Unknown',
                'role': m.role,
            })
        context['invites'] = invites

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
            _save_services(tenant_id)
        elif step_number == 2:
            _save_parts(tenant_id)
        elif step_number == 3:
            _save_invitations(tenant_id)
            flash('Setup complete! Welcome to RepairOS.', 'success')
            return redirect(url_for('onboarding.complete'))

        # Move to next step
        next_step = min(step_number + 1, 3)
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

    tenant_id = session.get('current_tenant_id')
    tenant_name = session.get('current_tenant_name', 'Your Organization')
    tenant_slug = session.get('current_tenant_slug', '')

    # Build summary with real data
    from app.models.service import Service
    from app.models.part import Part
    from app.models.tenant_membership import TenantMembership

    g.current_tenant_id = tenant_id

    services_count = len(Service.get_all_sorted())
    parts_count = len(Part.get_all_sorted())

    pending_invites = db.session.execute(
        db.select(db.func.count()).select_from(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.status == TenantMembership.STATUS_PENDING,
        )
    ).scalar() or 0

    summary = {
        'org_name': tenant_name,
        'services_count': services_count,
        'parts_count': parts_count,
        'invites_count': pending_invites,
    }

    return render_template('onboarding/complete.html',
                         tenant_name=tenant_name,
                         tenant_slug=tenant_slug,
                         summary=summary)


def _save_services(tenant_id):
    """Save service catalog (step 1)"""
    from app.models.service import Service
    g.current_tenant_id = tenant_id

    # Handle adding custom services
    service_name = sanitize_input(request.form.get('service_name', ''))
    cost = request.form.get('service_cost')
    category = sanitize_input(request.form.get('service_category', ''))
    duration = request.form.get('service_duration', '')

    if service_name and cost:
        try:
            estimated_minutes = None
            if duration:
                duration_str = duration.strip().lower()
                try:
                    estimated_minutes = int(duration_str)
                except ValueError:
                    # Try parsing "1 hour", "30 min", etc.
                    if 'hour' in duration_str:
                        estimated_minutes = int(float(duration_str.split()[0]) * 60)
                    elif 'min' in duration_str:
                        estimated_minutes = int(duration_str.split()[0])

            service = Service(
                tenant_id=tenant_id,
                service_name=service_name,
                cost=float(cost),
                category=category or 'General',
                estimated_duration_minutes=estimated_minutes,
                is_active=True,
            )
            db.session.add(service)
            db.session.commit()
            flash(f'Service "{service_name}" added!', 'success')
        except (ValueError, Exception) as e:
            logger.error(f"Failed to add service during onboarding: {e}")
            db.session.rollback()


def _save_parts(tenant_id):
    """Save parts catalog (step 2)"""
    from app.models.part import Part
    from app.extensions import db

    g.current_tenant_id = tenant_id

    # Handle adding custom parts
    part_name = sanitize_input(request.form.get('part_name', ''))
    cost = request.form.get('part_cost')
    sku = sanitize_input(request.form.get('part_sku', ''))
    category = sanitize_input(request.form.get('part_category', ''))
    supplier = sanitize_input(request.form.get('part_supplier', ''))

    if part_name and cost:
        try:
            part = Part(
                tenant_id=tenant_id,
                part_name=part_name,
                cost=float(cost),
                sku=sku or None,
                category=category or 'General',
                supplier=supplier or None,
                is_active=True,
            )
            db.session.add(part)
            db.session.commit()
            flash(f'Part "{part_name}" added!', 'success')
        except (ValueError, Exception) as e:
            logger.error(f"Failed to add part during onboarding: {e}")
            db.session.rollback()


def _save_invitations(tenant_id):
    """Save team invitations (step 3)"""
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

