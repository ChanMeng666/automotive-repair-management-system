"""
主要路由蓝图
包含首页、登录、公共功能等路由
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import date
import logging
from app.services.customer_service import CustomerService
from app.services.job_service import JobService
from app.services.billing_service import BillingService
from app.utils.decorators import handle_database_errors, log_function_call
from app.utils.validators import validate_customer_data, sanitize_input
from app.utils.security import csrf_protect, require_auth, InputSanitizer, SQLInjectionProtection
from app.utils.error_handler import ValidationError, BusinessLogicError

# 创建蓝图
main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# 初始化服务
customer_service = CustomerService()
job_service = JobService()
billing_service = BillingService()


@main_bp.route('/')
@handle_database_errors
@log_function_call
def index():
    """Home page - Display system overview and quick statistics"""
    try:
        # Get system statistics
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # Get recent work orders
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=5)
        
        # Get overdue bills
        overdue_bills = billing_service.get_overdue_bills()[:5]
        
        return render_template('index.html',
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills,
                             current_date=date.today())
        
    except Exception as e:
        logger.error(f"Home page loading failed: {e}")
        flash('System temporarily unavailable, please try again later', 'error')
        return render_template('index.html',
                             job_stats={},
                             billing_stats={},
                             recent_jobs=[],
                             overdue_bills=[],
                             current_date=date.today())


@main_bp.route('/login')
def login():
    """Login page (simplified version)"""
    return render_template('auth/login.html')


@main_bp.route('/login', methods=['POST'])
@csrf_protect
@handle_database_errors
def login_post():
    """Handle login submission"""
    from app.services.auth_service import AuthService

    username = InputSanitizer.sanitize_string(request.form.get('username', ''))
    password = request.form.get('password', '')
    user_type = InputSanitizer.sanitize_string(request.form.get('user_type', 'technician'))

    # Check for SQL injection
    if SQLInjectionProtection.scan_sql_injection(username):
        raise ValidationError("Username contains illegal characters")
    if SQLInjectionProtection.scan_sql_injection(user_type):
        raise ValidationError("User type contains illegal characters")

    if not username or not password:
        flash('Please enter username and password', 'error')
        return render_template('auth/login.html')

    # Use AuthService for authentication
    auth_service = AuthService()
    success, user_data, error_message = auth_service.authenticate(username, password, user_type)

    if success:
        session['user_id'] = user_data.get('user_id', username)
        session['username'] = user_data.get('username', username)
        session['user_type'] = user_data.get('role', user_type)
        session['logged_in'] = True

        flash(f'Welcome back, {username}!', 'success')

        # Redirect based on user type
        if user_data.get('role', user_type) == 'administrator':
            return redirect(url_for('administrator.dashboard'))
        else:
            return redirect(url_for('technician.current_jobs'))
    else:
        flash(error_message or 'Incorrect username or password', 'error')
        return render_template('auth/login.html')


@main_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have successfully logged out', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard')
@require_auth()
@handle_database_errors
@log_function_call
def dashboard():
    """Dashboard - System overview"""
    # Check if logged in (simplified version)
    if not session.get('logged_in'):
        flash('Please login first', 'warning')
        return redirect(url_for('main.login'))
    
    try:
        user_type = session.get('user_type', 'technician')
        
        # Get statistics
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # Get recent activities
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=10)
        overdue_bills = billing_service.get_overdue_bills()
        
        return render_template('dashboard.html',
                             user_type=user_type,
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills)
        
    except Exception as e:
        logger.error(f"Dashboard loading failed: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('dashboard.html',
                             user_type='technician',
                             job_stats={},
                             billing_stats={},
                             recent_jobs=[],
                             overdue_bills=[])


@main_bp.route('/api/search/customers')
@require_auth()
@handle_database_errors
def api_search_customers():
    """API: Search customers"""
    query = InputSanitizer.sanitize_string(request.args.get('q', ''))
    search_type = InputSanitizer.sanitize_string(request.args.get('type', 'both'))
    
    # Check for SQL injection
    if SQLInjectionProtection.scan_sql_injection(query):
        raise ValidationError("Search criteria contains illegal characters")
    
    if not query:
        return jsonify([])
    
    try:
        customers = customer_service.search_customers(query, search_type)
        return jsonify([{
            'customer_id': c.customer_id,
            'full_name': c.full_name,
            'email': c.email,
            'phone': c.phone
        } for c in customers])
        
    except Exception as e:
        logger.error(f"Customer search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500


@main_bp.route('/api/customers/<int:customer_id>')
@handle_database_errors
def api_get_customer(customer_id):
    """API: Get customer details"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        stats = customer_service.get_customer_statistics(customer_id)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get customer details failed: {e}")
        return jsonify({'error': 'Failed to get customer information'}), 500


@main_bp.route('/customers')
@handle_database_errors
@log_function_call
def customers():
    """Customer list page"""
    try:
        # Get search parameters
        search_query = sanitize_input(request.args.get('search', ''))
        search_type = sanitize_input(request.args.get('search_type', 'both'))
        
        # Search or get all customers
        if search_query:
            customers = customer_service.search_customers(search_query, search_type)
        else:
            customers = customer_service.get_all_customers()
        
        return render_template('customers/list.html',
                             customers=customers,
                             search_query=search_query,
                             search_type=search_type)
        
    except Exception as e:
        logger.error(f"Customer list loading failed: {e}")
        flash('Failed to load customer list', 'error')
        return render_template('customers/list.html',
                             customers=[],
                             search_query='',
                             search_type='both')


@main_bp.route('/customers/new')
def new_customer():
    """New customer page"""
    return render_template('customers/form.html',
                         customer=None,
                         action='create')


@main_bp.route('/customers', methods=['POST'])
@handle_database_errors
def create_customer():
    """Create new customer"""
    # Get form data
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', ''))
    }
    
    try:
        # Validate data
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            return render_template('customers/form.html',
                                 customer=customer_data,
                                 action='create')
        
        # Create customer
        success, errors, customer = customer_service.create_customer(customer_data)
        
        if success:
            flash(f'Customer {customer.full_name} created successfully!', 'success')
            return redirect(url_for('main.customers'))
        else:
            for error in errors:
                flash(error, 'error')
            return render_template('customers/form.html',
                                 customer=customer_data,
                                 action='create')
            
    except Exception as e:
        logger.error(f"Failed to create customer: {e}")
        flash('Failed to create customer, please try again later', 'error')
        return render_template('customers/form.html',
                             customer=customer_data,
                             action='create')


@main_bp.route('/customers/<int:customer_id>')
@handle_database_errors
@log_function_call
def customer_detail(customer_id):
    """Customer detail page"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('main.customers'))
        
        # Get customer statistics
        stats = customer_service.get_customer_statistics(customer_id)
        
        return render_template('customers/detail.html',
                             customer=customer,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Customer detail loading failed: {e}")
        flash('Failed to load customer details', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>/edit')
@handle_database_errors
def edit_customer(customer_id):
    """Edit customer page"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('main.customers'))
        
        return render_template('customers/form.html',
                             customer=customer,
                             action='edit')
        
    except Exception as e:
        logger.error(f"Failed to load customer edit page: {e}")
        flash('Failed to load edit page', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>', methods=['POST'])
@handle_database_errors
def update_customer(customer_id):
    """Update customer information"""
    # Get form data
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', ''))
    }
    
    try:
        # Validate data
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html',
                                 customer=customer,
                                 action='edit')
        
        # Update customer
        success, errors, customer = customer_service.update_customer(customer_id, customer_data)
        
        if success:
            flash(f'Customer {customer.full_name} updated successfully!', 'success')
            return redirect(url_for('main.customer_detail', customer_id=customer_id))
        else:
            for error in errors:
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html',
                                 customer=customer,
                                 action='edit')
            
    except Exception as e:
        logger.error(f"Failed to update customer: {e}")
        flash('Failed to update customer, please try again later', 'error')
        customer = customer_service.get_customer_by_id(customer_id)
        return render_template('customers/form.html',
                             customer=customer,
                             action='edit')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/help')
def help_page():
    """Help page"""
    return render_template('help.html')


# Error handling
@main_bp.errorhandler(404)
def not_found_error(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('errors/500.html'), 500 