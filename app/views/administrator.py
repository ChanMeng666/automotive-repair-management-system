"""
管理员路由蓝图
包含客户管理、账单管理、逾期账单处理等功能
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import date, timedelta
import logging
from app.services.customer_service import CustomerService
from app.services.job_service import JobService
from app.services.billing_service import BillingService
from app.utils.decorators import handle_database_errors, log_function_call, validate_pagination
from app.utils.validators import sanitize_input, validate_positive_integer

# 创建蓝图
administrator_bp = Blueprint('administrator', __name__)
logger = logging.getLogger(__name__)

# 初始化服务
customer_service = CustomerService()
job_service = JobService()
billing_service = BillingService()


def require_admin_login():
    """Check administrator login status"""
    if not session.get('logged_in'):
        flash('Please login first', 'warning')
        return redirect(url_for('main.login'))

    if session.get('user_type') != 'administrator':
        flash('Administrator privileges required', 'error')
        return redirect(url_for('main.index'))
    
    return None


@administrator_bp.route('/dashboard')
@handle_database_errors
@log_function_call
def dashboard():
    """Administrator dashboard"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # Get system statistics
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # Get customer statistics
        total_customers = len(customer_service.get_all_customers())
        customers_with_unpaid = customer_service.get_customers_with_filter(has_unpaid=True)
        customers_with_overdue = customer_service.get_customers_with_filter(has_overdue=True)
        
        # Get recent activities
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=5)
        overdue_bills = billing_service.get_overdue_bills()[:5]
        
        return render_template('administrator/dashboard.html',
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             total_customers=total_customers,
                             customers_with_unpaid=len(customers_with_unpaid),
                             customers_with_overdue=len(customers_with_overdue),
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills,
                             current_date=date.today())
        
    except Exception as e:
        logger.error(f"Administrator dashboard loading failed: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('administrator/dashboard.html',
                             job_stats={},
                             billing_stats={},
                             total_customers=0,
                             customers_with_unpaid=0,
                             customers_with_overdue=0,
                             recent_jobs=[],
                             overdue_bills=[],
                             current_date=date.today())


@administrator_bp.route('/customers')
@validate_pagination
@handle_database_errors
@log_function_call
def customer_list(page=1, per_page=20):
    """客户管理页面"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取过滤参数
        filter_type = sanitize_input(request.args.get('filter', 'all'))
        search_query = sanitize_input(request.args.get('search', ''))
        
        # 根据过滤条件获取客户
        if filter_type == 'unpaid':
            customers = customer_service.get_customers_with_filter(has_unpaid=True)
        elif filter_type == 'overdue':
            customers = customer_service.get_customers_with_filter(has_overdue=True)
        elif search_query:
            customers_obj = customer_service.search_customers(search_query)
            customers = [c.to_dict() for c in customers_obj]
            # 添加统计信息
            for customer in customers:
                customer['total_unpaid'] = customer_service.get_customer_by_id(customer['customer_id']).get_total_unpaid_amount()
                customer['has_overdue'] = customer_service.get_customer_by_id(customer['customer_id']).has_overdue_bills()
        else:
            customers_obj = customer_service.get_all_customers()
            customers = []
            for c in customers_obj:
                customer_data = c.to_dict()
                customer_data['total_unpaid'] = c.get_total_unpaid_amount()
                customer_data['has_overdue'] = c.has_overdue_bills()
                customers.append(customer_data)
        
        # 简单分页
        total = len(customers)
        start = (page - 1) * per_page
        end = start + per_page
        customers_page = customers[start:end]
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('administrator/customer_list.html',
                             customers=customers_page,
                             page=page,
                             per_page=per_page,
                             total=total,
                             total_pages=total_pages,
                             filter_type=filter_type,
                             search_query=search_query)
        
    except Exception as e:
        logger.error(f"客户管理页面加载失败: {e}")
        flash('Failed to load customer list', 'error')
        return render_template('administrator/customer_list.html',
                             customers=[],
                             page=1,
                             per_page=per_page,
                             total=0,
                             total_pages=0,
                             filter_type='all',
                             search_query='')


@administrator_bp.route('/billing')
@handle_database_errors
@log_function_call
def billing_management():
    """账单管理页面"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取过滤参数
        filter_type = sanitize_input(request.args.get('filter', 'unpaid'))
        customer_name = sanitize_input(request.args.get('customer', ''))
        
        # 获取账单数据
        if filter_type == 'overdue':
            bills = billing_service.get_overdue_bills()
        elif filter_type == 'all':
            bills = billing_service.get_all_bills_with_status()
        else:  # unpaid
            bills = billing_service.get_unpaid_bills(customer_name if customer_name != 'Choose...' else None)
        
        # 获取客户名称列表（用于下拉选择）
        customers = customer_service.get_all_customers()
        customer_names = [f"{c.first_name} {c.family_name}".strip() for c in customers]
        customer_names = list(set(customer_names))  # 去重
        customer_names.sort()
        
        # 获取账单统计
        billing_stats = billing_service.get_billing_statistics()
        
        return render_template('administrator/billing.html',
                             bills=bills,
                             filter_type=filter_type,
                             customer_name=customer_name,
                             customer_names=customer_names,
                             billing_stats=billing_stats)
        
    except Exception as e:
        logger.error(f"账单管理页面加载失败: {e}")
        flash('Failed to load billing management page', 'error')
        return render_template('administrator/billing.html',
                             bills=[],
                             filter_type='unpaid',
                             customer_name='',
                             customer_names=[],
                             billing_stats={})


@administrator_bp.route('/overdue-bills')
@handle_database_errors
@log_function_call
def overdue_bills():
    """逾期账单页面"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取逾期天数阈值
        days_threshold = request.args.get('days', 14, type=int)
        if days_threshold < 1:
            days_threshold = 14
        
        # 获取逾期账单
        overdue_bills_list = billing_service.get_overdue_bills(days_threshold)
        
        # 计算总金额
        total_overdue_amount = sum(float(bill.get('total_cost', 0)) for bill in overdue_bills_list)
        
        return render_template('administrator/overdue_bills.html',
                             overdue_bills=overdue_bills_list,
                             total_overdue_amount=total_overdue_amount,
                             days_threshold=days_threshold,
                             total_count=len(overdue_bills_list))
        
    except Exception as e:
        logger.error(f"逾期账单页面加载失败: {e}")
        flash('Failed to load overdue bills page', 'error')
        return render_template('administrator/overdue_bills.html',
                             overdue_bills=[],
                             total_overdue_amount=0,
                             days_threshold=14,
                             total_count=0)


@administrator_bp.route('/pay-bills')
@handle_database_errors
@log_function_call
def pay_bills():
    """付款处理页面"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取客户名称过滤参数
        customer_name = sanitize_input(request.args.get('customer', ''))
        
        # 获取未付款账单
        unpaid_bills = billing_service.get_unpaid_bills(customer_name if customer_name != 'Choose...' else None)
        
        # 获取客户名称列表
        customers = customer_service.get_all_customers()
        customer_names = [f"{c.first_name} {c.family_name}".strip() for c in customers]
        customer_names = list(set(customer_names))
        customer_names.sort()
        
        return render_template('administrator/pay_bills.html',
                             unpaid_bills=unpaid_bills,
                             customer_name=customer_name,
                             customer_names=customer_names)
        
    except Exception as e:
        logger.error(f"付款处理页面加载失败: {e}")
        flash('Failed to load payment processing page', 'error')
        return render_template('administrator/pay_bills.html',
                             unpaid_bills=[],
                             customer_name='',
                             customer_names=[])


@administrator_bp.route('/customers/<int:customer_id>/pay', methods=['POST'])
@handle_database_errors
def pay_customer_bills(customer_id):
    """标记客户的所有账单为已付款"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        success, errors, count = billing_service.mark_customer_bills_as_paid(customer_id)
        
        if success:
            flash(f'Successfully marked {count} bills as paid!', 'success')
        else:
            for error in errors:
                flash(error, 'error')
        
        return redirect(url_for('administrator.customer_list'))
        
    except Exception as e:
        logger.error(f"Failed to mark customer bills as paid: {e}")
        flash('Failed to mark payment, please try again later', 'error')
        return redirect(url_for('administrator.customer_list'))


@administrator_bp.route('/jobs/<int:job_id>/pay', methods=['POST'])
@handle_database_errors
def pay_single_bill(job_id):
    """Mark single work order as paid"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        success, errors = billing_service.mark_job_as_paid(job_id)
        
        if success:
            flash('Bill has been marked as paid!', 'success')
        else:
            for error in errors:
                flash(error, 'error')
        
        # 根据来源页面重定向
        return_page = sanitize_input(request.form.get('return_page', 'pay_bills'))
        if return_page == 'overdue_bills':
            return redirect(url_for('administrator.overdue_bills'))
        else:
            return redirect(url_for('administrator.pay_bills'))
        
    except Exception as e:
        logger.error(f"Failed to mark bill as paid: {e}")
        flash('Failed to mark payment, please try again later', 'error')
        return redirect(url_for('administrator.pay_bills'))


@administrator_bp.route('/reports')
@handle_database_errors
@log_function_call
def reports():
    """报表页面"""
    redirect_response = require_admin_login()
    if redirect_response:
        return redirect_response
    
    try:
        # 获取各种统计数据
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # 获取客户统计
        total_customers = len(customer_service.get_all_customers())
        customers_with_unpaid = customer_service.get_customers_with_filter(has_unpaid=True)
        customers_with_overdue = customer_service.get_customers_with_filter(has_overdue=True)
        
        # 计算本月和上月的对比数据
        today = date.today()
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        # 这里可以添加更多的统计分析
        report_data = {
            'job_stats': job_stats,
            'billing_stats': billing_stats,
            'customer_stats': {
                'total_customers': total_customers,
                'customers_with_unpaid': len(customers_with_unpaid),
                'customers_with_overdue': len(customers_with_overdue),
                'customer_payment_rate': ((total_customers - len(customers_with_unpaid)) / total_customers * 100) if total_customers > 0 else 0
            },
            'period_info': {
                'current_month': current_month_start.strftime('%Y年%m月'),
                'last_month': last_month_start.strftime('%Y年%m月'),
                'generated_date': today.strftime('%Y-%m-%d')
            }
        }
        
        return render_template('administrator/reports.html',
                             report_data=report_data)
        
    except Exception as e:
        logger.error(f"报表页面加载失败: {e}")
        flash('Failed to load reports', 'error')
        return render_template('administrator/reports.html',
                             report_data={})


# API接口
@administrator_bp.route('/api/customers/<int:customer_id>/billing-summary')
@handle_database_errors
def api_customer_billing_summary(customer_id):
    """API: 获取客户账单汇总"""
    try:
        summary = billing_service.get_customer_billing_summary(customer_id)
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"获取客户账单汇总失败: {e}")
        return jsonify({'error': '获取账单汇总失败'}), 500


@administrator_bp.route('/api/billing/statistics')
@handle_database_errors
def api_billing_statistics():
    """API: 获取账单统计信息"""
    try:
        stats = billing_service.get_billing_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取账单统计失败: {e}")
        return jsonify({'error': '获取统计信息失败'}), 500


@administrator_bp.route('/api/dashboard/summary')
@handle_database_errors
def api_dashboard_summary():
    """API: 获取仪表板汇总信息"""
    try:
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        
        # 客户统计
        total_customers = len(customer_service.get_all_customers())
        customers_with_unpaid = customer_service.get_customers_with_filter(has_unpaid=True)
        customers_with_overdue = customer_service.get_customers_with_filter(has_overdue=True)
        
        summary = {
            'jobs': job_stats,
            'billing': billing_stats,
            'customers': {
                'total': total_customers,
                'with_unpaid': len(customers_with_unpaid),
                'with_overdue': len(customers_with_overdue)
            },
            'alerts': {
                'overdue_bills': len(billing_service.get_overdue_bills()),
                'pending_jobs': job_stats.get('pending_jobs', 0)
            }
        }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"获取仪表板汇总失败: {e}")
        return jsonify({'error': '获取汇总信息失败'}), 500


@administrator_bp.route('/api/export/customers')
@handle_database_errors
def api_export_customers():
    """API: 导出客户数据（简化版本）"""
    try:
        customers = customer_service.get_all_customers()
        customer_data = []
        
        for c in customers:
            customer_info = c.to_dict()
            customer_info['total_unpaid'] = c.get_total_unpaid_amount()
            customer_info['has_overdue'] = c.has_overdue_bills()
            customer_data.append(customer_info)
        
        return jsonify({
            'data': customer_data,
            'export_date': date.today().isoformat(),
            'total_count': len(customer_data)
        })
        
    except Exception as e:
        logger.error(f"导出客户数据失败: {e}")
        return jsonify({'error': '导出数据失败'}), 500


@administrator_bp.route('/api/customers/<int:customer_id>/summary')
@handle_database_errors
def api_customer_summary(customer_id):
    """API: 获取客户汇总信息"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({'error': '客户不存在'}), 404
        
        stats = customer_service.get_customer_statistics(customer_id)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取客户汇总失败: {e}")
        return jsonify({'error': '获取客户信息失败'}), 500 