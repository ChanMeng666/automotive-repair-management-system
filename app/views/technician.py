"""
Technician Routes Blueprint
Contains work order management, service and parts addition functionality
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import date, datetime
import logging
from app.services.job_service import JobService
from app.services.customer_service import CustomerService
from app.models.service import Service
from app.models.part import Part
from app.utils.decorators import handle_database_errors, log_function_call, validate_pagination
from app.utils.validators import sanitize_input, validate_positive_integer, validate_date

# Create blueprint
technician_bp = Blueprint('technician', __name__)
logger = logging.getLogger(__name__)

# Initialize services
job_service = JobService()
customer_service = CustomerService()


def require_technician_login():
    """Check technician login status"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('auth.login'))
    return None


@technician_bp.route('/current-jobs')
@validate_pagination
@handle_database_errors
@log_function_call
def current_jobs(page=1, per_page=10):
    """Current work order list"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        jobs, total, total_pages = job_service.get_current_jobs(page, per_page)

        return render_template('technician/current_jobs.html',
                             jobs=jobs,
                             page=page,
                             per_page=per_page,
                             total=total,
                             total_pages=total_pages)

    except Exception as e:
        logger.error(f"Failed to get current work orders: {e}")
        flash('Failed to load work orders', 'error')
        return render_template('technician/current_jobs.html',
                             jobs=[],
                             page=1,
                             per_page=per_page,
                             total=0,
                             total_pages=0)


@technician_bp.route('/jobs/<int:job_id>')
@handle_database_errors
@log_function_call
def job_detail(job_id):
    """Work order detail page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_details = job_service.get_job_details(job_id)

        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))

        return render_template('technician/job_detail.html',
                             job_details=job_details)

    except Exception as e:
        logger.error(f"Failed to get work order details (ID: {job_id}): {e}")
        flash('Failed to load work order details', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/modify')
@handle_database_errors
@log_function_call
def modify_job(job_id):
    """Modify work order page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_details = job_service.get_job_details(job_id)

        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))

        if job_details.get('job_completed'):
            flash('Cannot modify completed work order', 'warning')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        return render_template('technician/modify_job.html',
                             job_details=job_details)

    except Exception as e:
        logger.error(f"Failed to load work order modification page (ID: {job_id}): {e}")
        flash('Failed to load modification page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/add-service', methods=['POST'])
@handle_database_errors
def add_service_to_job(job_id):
    """Add service to work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        service_id = request.form.get('service_id', type=int)
        quantity = request.form.get('quantity', type=int)

        if not service_id or not validate_positive_integer(service_id):
            flash('Please select a valid service', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

        if not quantity or not validate_positive_integer(quantity):
            flash('Please enter a valid quantity', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

        success, errors = job_service.add_service_to_job(job_id, service_id, quantity)

        if success:
            flash('Service added successfully!', 'success')
        else:
            for error in errors:
                flash(error, 'error')

        return redirect(url_for('technician.modify_job', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to add service: {e}")
        flash('Failed to add service, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/add-part', methods=['POST'])
@handle_database_errors
def add_part_to_job(job_id):
    """Add part to work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        part_id = request.form.get('part_id', type=int)
        quantity = request.form.get('quantity', type=int)

        if not part_id or not validate_positive_integer(part_id):
            flash('Please select a valid part', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

        if not quantity or not validate_positive_integer(quantity):
            flash('Please enter a valid quantity', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

        success, errors = job_service.add_part_to_job(job_id, part_id, quantity)

        if success:
            flash('Part added successfully!', 'success')
        else:
            for error in errors:
                flash(error, 'error')

        return redirect(url_for('technician.modify_job', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to add part: {e}")
        flash('Failed to add part, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/complete', methods=['POST'])
@handle_database_errors
def complete_job(job_id):
    """Mark work order as completed"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        success, errors = job_service.mark_job_as_completed(job_id)

        if success:
            flash('Work order marked as completed!', 'success')
            return redirect(url_for('technician.job_detail', job_id=job_id))
        else:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to mark work order as completed: {e}")
        flash('Failed to mark as completed, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/new')
@handle_database_errors
def new_job():
    """Create new work order page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        customers = customer_service.get_all_customers()

        return render_template('technician/new_job.html',
                             customers=customers,
                             min_date=date.today().isoformat())

    except Exception as e:
        logger.error(f"Failed to load new work order page: {e}")
        flash('Failed to load page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs', methods=['POST'])
@handle_database_errors
def create_job():
    """Create new work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        customer_id = request.form.get('customer_id', type=int)
        job_date_str = sanitize_input(request.form.get('job_date', ''))

        if not customer_id or not validate_positive_integer(customer_id):
            flash('Please select a valid customer', 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

        if not job_date_str or not validate_date(job_date_str):
            flash('Please enter a valid work date', 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

        job_date = datetime.strptime(job_date_str, '%Y-%m-%d').date()

        success, errors, job = job_service.create_job(customer_id, job_date)

        if success:
            flash('Work order created successfully!', 'success')
            return redirect(url_for('technician.modify_job', job_id=job.job_id))
        else:
            for error in errors:
                flash(error, 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        flash('Failed to create work order, please try again later', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/services')
@handle_database_errors
@log_function_call
def services():
    """Service list page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        services = Service.get_all_sorted()
        return render_template('technician/services.html',
                             services=services)

    except Exception as e:
        logger.error(f"Failed to get service list: {e}")
        flash('Failed to load service list', 'error')
        return render_template('technician/services.html',
                             services=[])


@technician_bp.route('/parts')
@handle_database_errors
@log_function_call
def parts():
    """Parts list page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        parts = Part.get_all_sorted()
        return render_template('technician/parts.html',
                             parts=parts)

    except Exception as e:
        logger.error(f"Failed to get parts list: {e}")
        flash('Failed to load parts list', 'error')
        return render_template('technician/parts.html',
                             parts=[])


@technician_bp.route('/dashboard')
@handle_database_errors
@log_function_call
def dashboard():
    """Technician dashboard"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_stats = job_service.get_job_statistics()
        today = date.today()
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=10)

        today_jobs = [job for job in recent_jobs
                     if job.get('job_date') == today or
                        (isinstance(job.get('job_date'), str) and
                         job.get('job_date').startswith(str(today)))]

        return render_template('technician/dashboard.html',
                             job_stats=job_stats,
                             recent_jobs=recent_jobs[:5],
                             today_jobs=today_jobs,
                             current_date=today)

    except Exception as e:
        logger.error(f"Technician dashboard loading failed: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('technician/dashboard.html',
                             job_stats={},
                             recent_jobs=[],
                             today_jobs=[],
                             current_date=date.today())


# API endpoints
@technician_bp.route('/api/services')
@handle_database_errors
def api_get_services():
    """API: Get all services"""
    try:
        services = Service.get_all_sorted()
        return jsonify([{
            'service_id': s.service_id,
            'service_name': s.service_name,
            'cost': float(s.cost) if s.cost else 0
        } for s in services])

    except Exception as e:
        logger.error(f"Failed to get services API: {e}")
        return jsonify({'error': 'Failed to get service list'}), 500


@technician_bp.route('/api/parts')
@handle_database_errors
def api_get_parts():
    """API: Get all parts"""
    try:
        parts = Part.get_all_sorted()
        return jsonify([{
            'part_id': p.part_id,
            'part_name': p.part_name,
            'cost': float(p.cost) if p.cost else 0
        } for p in parts])

    except Exception as e:
        logger.error(f"Failed to get parts API: {e}")
        return jsonify({'error': 'Failed to get parts list'}), 500


@technician_bp.route('/api/jobs/<int:job_id>/status')
@handle_database_errors
def api_get_job_status(job_id):
    """API: Get work order status"""
    try:
        job = job_service.get_job_by_id(job_id)
        if not job:
            return jsonify({'error': 'Work order not found'}), 404

        return jsonify({
            'job_id': job.job_id,
            'completed': bool(job.completed),
            'paid': bool(job.paid),
            'total_cost': float(job.total_cost) if job.total_cost else 0,
            'status_text': job.status_text
        })

    except Exception as e:
        logger.error(f"Failed to get work order status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500
