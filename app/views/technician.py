"""
技术员路由蓝图
包含工作订单管理、服务和零件添加等功能
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

# 创建蓝图
technician_bp = Blueprint('technician', __name__)
logger = logging.getLogger(__name__)

# 初始化服务
job_service = JobService()
customer_service = CustomerService()


def require_technician_login():
    """检查技术员登录状态"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('main.login'))
    return None


@technician_bp.route('/current-jobs')
@validate_pagination
@handle_database_errors
@log_function_call
def current_jobs(page=1, per_page=10):
    """当前工作订单列表"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取当前未完成的工作订单
        jobs, total, total_pages = job_service.get_current_jobs(page, per_page)
        
        return render_template('technician/current_jobs.html',
                             jobs=jobs,
                             page=page,
                             per_page=per_page,
                             total=total,
                             total_pages=total_pages)
        
    except Exception as e:
        logger.error(f"获取当前工作订单失败: {e}")
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
    """工作订单详情页面"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取工作订单详细信息
        job_details = job_service.get_job_details(job_id)
        
        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))
        
        return render_template('technician/job_detail.html',
                             job_details=job_details)
        
    except Exception as e:
        logger.error(f"获取工作订单详情失败 (ID: {job_id}): {e}")
        flash('Failed to load work order details', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/modify')
@handle_database_errors
@log_function_call
def modify_job(job_id):
    """修改工作订单页面"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取工作订单详细信息
        job_details = job_service.get_job_details(job_id)
        
        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))
        
        # 检查工作订单是否已完成
        if job_details.get('job_completed'):
            flash('Cannot modify completed work order', 'warning')
            return redirect(url_for('technician.job_detail', job_id=job_id))
        
        return render_template('technician/modify_job.html',
                             job_details=job_details)
        
    except Exception as e:
        logger.error(f"加载工作订单修改页面失败 (ID: {job_id}): {e}")
        flash('Failed to load modification page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/add-service', methods=['POST'])
@handle_database_errors
def add_service_to_job(job_id):
    """为工作订单添加服务"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        service_id = request.form.get('service_id', type=int)
        quantity = request.form.get('quantity', type=int)
        
        # 验证输入
        if not service_id or not validate_positive_integer(service_id):
            flash('Please select a valid service', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))
        
        if not quantity or not validate_positive_integer(quantity):
            flash('Please enter a valid quantity', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))
        
        # 添加服务
        success, errors = job_service.add_service_to_job(job_id, service_id, quantity)
        
        if success:
            flash('Service added successfully!', 'success')
        else:
            for error in errors:
                flash(error, 'error')
        
        return redirect(url_for('technician.modify_job', job_id=job_id))
        
    except Exception as e:
        logger.error(f"添加服务失败: {e}")
        flash('Failed to add service, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/add-part', methods=['POST'])
@handle_database_errors
def add_part_to_job(job_id):
    """为工作订单添加零件"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        part_id = request.form.get('part_id', type=int)
        quantity = request.form.get('quantity', type=int)
        
        # 验证输入
        if not part_id or not validate_positive_integer(part_id):
            flash('Please select a valid part', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))
        
        if not quantity or not validate_positive_integer(quantity):
            flash('Please enter a valid quantity', 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))
        
        # 添加零件
        success, errors = job_service.add_part_to_job(job_id, part_id, quantity)
        
        if success:
            flash('Part added successfully!', 'success')
        else:
            for error in errors:
                flash(error, 'error')
        
        return redirect(url_for('technician.modify_job', job_id=job_id))
        
    except Exception as e:
        logger.error(f"添加零件失败: {e}")
        flash('Failed to add part, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/complete', methods=['POST'])
@handle_database_errors
def complete_job(job_id):
    """标记工作订单为完成"""
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
        logger.error(f"标记工作订单完成失败: {e}")
        flash('Failed to mark as completed, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/new')
@handle_database_errors
def new_job():
    """创建新工作订单页面"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取所有客户
        customers = customer_service.get_all_customers()
        
        return render_template('technician/new_job.html',
                             customers=customers,
                             min_date=date.today().isoformat())
        
    except Exception as e:
        logger.error(f"加载新建工作订单页面失败: {e}")
        flash('Failed to load page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs', methods=['POST'])
@handle_database_errors
def create_job():
    """创建新工作订单"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        customer_id = request.form.get('customer_id', type=int)
        job_date_str = sanitize_input(request.form.get('job_date', ''))
        
        # 验证输入
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
        
        # 转换日期
        job_date = datetime.strptime(job_date_str, '%Y-%m-%d').date()
        
        # 创建工作订单
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
        logger.error(f"创建工作订单失败: {e}")
        flash('Failed to create work order, please try again later', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/services')
@handle_database_errors
@log_function_call
def services():
    """服务列表页面"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        services = Service.get_all_sorted()
        return render_template('technician/services.html',
                             services=services)
        
    except Exception as e:
        logger.error(f"获取服务列表失败: {e}")
        flash('Failed to load service list', 'error')
        return render_template('technician/services.html',
                             services=[])


@technician_bp.route('/parts')
@handle_database_errors
@log_function_call
def parts():
    """零件列表页面"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        parts = Part.get_all_sorted()
        return render_template('technician/parts.html',
                             parts=parts)
        
    except Exception as e:
        logger.error(f"获取零件列表失败: {e}")
        flash('Failed to load parts list', 'error')
        return render_template('technician/parts.html',
                             parts=[])


@technician_bp.route('/dashboard')
@handle_database_errors
@log_function_call
def dashboard():
    """技术员仪表板"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取统计信息
        job_stats = job_service.get_job_statistics()
        
        # 获取今天的工作订单
        today = date.today()
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=10)
        
        # 过滤出今天的订单
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
        logger.error(f"技术员仪表板加载失败: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('technician/dashboard.html',
                             job_stats={},
                             recent_jobs=[],
                             today_jobs=[],
                             current_date=date.today())


# API接口
@technician_bp.route('/api/services')
@handle_database_errors
def api_get_services():
    """API: 获取所有服务"""
    try:
        services = Service.get_all_sorted()
        return jsonify([{
            'service_id': s.service_id,
            'service_name': s.service_name,
            'cost': float(s.cost) if s.cost else 0
        } for s in services])
        
    except Exception as e:
        logger.error(f"获取服务列表API失败: {e}")
        return jsonify({'error': '获取服务列表失败'}), 500


@technician_bp.route('/api/parts')
@handle_database_errors
def api_get_parts():
    """API: 获取所有零件"""
    try:
        parts = Part.get_all_sorted()
        return jsonify([{
            'part_id': p.part_id,
            'part_name': p.part_name,
            'cost': float(p.cost) if p.cost else 0
        } for p in parts])
        
    except Exception as e:
        logger.error(f"获取零件列表API失败: {e}")
        return jsonify({'error': '获取零件列表失败'}), 500


@technician_bp.route('/api/jobs/<int:job_id>/status')
@handle_database_errors
def api_get_job_status(job_id):
    """API: 获取工作订单状态"""
    try:
        job = job_service.get_job_by_id(job_id)
        if not job:
            return jsonify({'error': '工作订单不存在'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'completed': bool(job.completed),
            'paid': bool(job.paid),
            'total_cost': float(job.total_cost) if job.total_cost else 0,
            'status_text': job.status_text
        })
        
    except Exception as e:
        logger.error(f"获取工作订单状态失败: {e}")
        return jsonify({'error': '获取状态失败'}), 500 