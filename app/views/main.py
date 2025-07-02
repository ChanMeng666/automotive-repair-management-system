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
    """首页 - 显示系统概览和快速统计"""
    try:
        # 获取系统统计信息
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # 获取最近的工作订单
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=5)
        
        # 获取逾期账单
        overdue_bills = billing_service.get_overdue_bills()[:5]
        
        return render_template('index.html',
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills,
                             current_date=date.today())
        
    except Exception as e:
        logger.error(f"首页加载失败: {e}")
        flash('系统暂时不可用，请稍后重试', 'error')
        return render_template('index.html',
                             job_stats={},
                             billing_stats={},
                             recent_jobs=[],
                             overdue_bills=[],
                             current_date=date.today())


@main_bp.route('/login')
def login():
    """登录页面（简化版本）"""
    return render_template('auth/login.html')


@main_bp.route('/login', methods=['POST'])
@csrf_protect
@handle_database_errors
def login_post():
    """处理登录提交（简化版本）"""
    username = InputSanitizer.sanitize_string(request.form.get('username', ''))
    password = request.form.get('password', '')
    user_type = InputSanitizer.sanitize_string(request.form.get('user_type', 'technician'))
    
    # 检查SQL注入
    if SQLInjectionProtection.scan_sql_injection(username):
        raise ValidationError("用户名包含非法字符")
    if SQLInjectionProtection.scan_sql_injection(user_type):
        raise ValidationError("用户类型包含非法字符")
    
    # 简化的登录验证（实际项目中需要完整的认证系统）
    if username and password:
        # 这里应该进行实际的用户验证
        # 目前为演示目的，使用简单的验证
        if password == '123456':  # 临时验证逻辑
            session['user_id'] = username
            session['user_type'] = user_type
            session['logged_in'] = True
            
            flash(f'欢迎回来，{username}！', 'success')
            
            # 根据用户类型重定向
            if user_type == 'administrator':
                return redirect(url_for('administrator.dashboard'))
            else:
                return redirect(url_for('technician.current_jobs'))
        else:
            flash('用户名或密码错误', 'error')
    else:
        flash('请输入用户名和密码', 'error')
    
    return render_template('auth/login.html')


@main_bp.route('/logout')
def logout():
    """注销"""
    session.clear()
    flash('您已成功注销', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard')
@require_auth()
@handle_database_errors
@log_function_call
def dashboard():
    """仪表板 - 系统概览"""
    # 检查是否已登录（简化版本）
    if not session.get('logged_in'):
        flash('请先登录', 'warning')
        return redirect(url_for('main.login'))
    
    try:
        user_type = session.get('user_type', 'technician')
        
        # 获取统计数据
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # 获取最近活动
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=10)
        overdue_bills = billing_service.get_overdue_bills()
        
        return render_template('dashboard.html',
                             user_type=user_type,
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills)
        
    except Exception as e:
        logger.error(f"仪表板加载失败: {e}")
        flash('加载仪表板失败', 'error')
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
    """API: 搜索客户"""
    query = InputSanitizer.sanitize_string(request.args.get('q', ''))
    search_type = InputSanitizer.sanitize_string(request.args.get('type', 'both'))
    
    # 检查SQL注入
    if SQLInjectionProtection.scan_sql_injection(query):
        raise ValidationError("搜索条件包含非法字符")
    
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
        logger.error(f"搜索客户失败: {e}")
        return jsonify({'error': '搜索失败'}), 500


@main_bp.route('/api/customers/<int:customer_id>')
@handle_database_errors
def api_get_customer(customer_id):
    """API: 获取客户详情"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({'error': '客户不存在'}), 404
        
        stats = customer_service.get_customer_statistics(customer_id)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取客户详情失败: {e}")
        return jsonify({'error': '获取客户信息失败'}), 500


@main_bp.route('/customers')
@handle_database_errors
@log_function_call
def customers():
    """客户列表页面"""
    try:
        # 获取搜索参数
        search_query = sanitize_input(request.args.get('search', ''))
        search_type = sanitize_input(request.args.get('search_type', 'both'))
        
        # 搜索或获取所有客户
        if search_query:
            customers = customer_service.search_customers(search_query, search_type)
        else:
            customers = customer_service.get_all_customers()
        
        return render_template('customers/list.html',
                             customers=customers,
                             search_query=search_query,
                             search_type=search_type)
        
    except Exception as e:
        logger.error(f"客户列表加载失败: {e}")
        flash('加载客户列表失败', 'error')
        return render_template('customers/list.html',
                             customers=[],
                             search_query='',
                             search_type='both')


@main_bp.route('/customers/new')
def new_customer():
    """新建客户页面"""
    return render_template('customers/form.html',
                         customer=None,
                         action='create')


@main_bp.route('/customers', methods=['POST'])
@handle_database_errors
def create_customer():
    """创建新客户"""
    # 获取表单数据
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', ''))
    }
    
    try:
        # 验证数据
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            return render_template('customers/form.html',
                                 customer=customer_data,
                                 action='create')
        
        # 创建客户
        success, errors, customer = customer_service.create_customer(customer_data)
        
        if success:
            flash(f'客户 {customer.full_name} 创建成功！', 'success')
            return redirect(url_for('main.customers'))
        else:
            for error in errors:
                flash(error, 'error')
            return render_template('customers/form.html',
                                 customer=customer_data,
                                 action='create')
            
    except Exception as e:
        logger.error(f"创建客户失败: {e}")
        flash('创建客户失败，请稍后重试', 'error')
        return render_template('customers/form.html',
                             customer=customer_data,
                             action='create')


@main_bp.route('/customers/<int:customer_id>')
@handle_database_errors
@log_function_call
def customer_detail(customer_id):
    """客户详情页面"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('main.customers'))
        
        # 获取客户统计信息
        stats = customer_service.get_customer_statistics(customer_id)
        
        return render_template('customers/detail.html',
                             customer=customer,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"客户详情加载失败: {e}")
        flash('加载客户详情失败', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>/edit')
@handle_database_errors
def edit_customer(customer_id):
    """编辑客户页面"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('客户不存在', 'error')
            return redirect(url_for('main.customers'))
        
        return render_template('customers/form.html',
                             customer=customer,
                             action='edit')
        
    except Exception as e:
        logger.error(f"加载客户编辑页面失败: {e}")
        flash('加载编辑页面失败', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>', methods=['POST'])
@handle_database_errors
def update_customer(customer_id):
    """更新客户信息"""
    # 获取表单数据
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', ''))
    }
    
    try:
        # 验证数据
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html',
                                 customer=customer,
                                 action='edit')
        
        # 更新客户
        success, errors, customer = customer_service.update_customer(customer_id, customer_data)
        
        if success:
            flash(f'客户 {customer.full_name} 更新成功！', 'success')
            return redirect(url_for('main.customer_detail', customer_id=customer_id))
        else:
            for error in errors:
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html',
                                 customer=customer,
                                 action='edit')
            
    except Exception as e:
        logger.error(f"更新客户失败: {e}")
        flash('更新客户失败，请稍后重试', 'error')
        customer = customer_service.get_customer_by_id(customer_id)
        return render_template('customers/form.html',
                             customer=customer,
                             action='edit')


@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@main_bp.route('/help')
def help_page():
    """帮助页面"""
    return render_template('help.html')


# 错误处理
@main_bp.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('errors/500.html'), 500 