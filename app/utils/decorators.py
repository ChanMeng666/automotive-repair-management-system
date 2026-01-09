"""
Decorator utility module
Contains decorators for authentication, authorization, logging, and error handling
"""
import functools
import logging
from typing import Callable, Any, List, Union
import time
from flask import jsonify, flash, request, session, redirect, url_for, abort
from app.utils.database import DatabaseError, ValidationError


def handle_database_errors(func: Callable) -> Callable:
    """
    数据库错误处理装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            logging.error(f"数据库错误在 {func.__name__}: {e}")
            flash(f"Database operation failed: {e}", 'error')
            return None
        except ValidationError as e:
            logging.warning(f"验证错误在 {func.__name__}: {e}")
            flash(f"Data validation failed: {e}", 'warning')
            return None
        except Exception as e:
            logging.error(f"未知错误在 {func.__name__}: {e}")
            flash("System error, please try again later", 'error')
            return None
    
    return wrapper


def log_function_call(func: Callable) -> Callable:
    """
    函数调用日志装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        # 记录函数调用开始
        logger.debug(f"调用函数 {func.__name__} 开始")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行成功，耗时: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"函数 {func.__name__} 执行失败，耗时: {execution_time:.3f}秒，错误: {e}")
            raise
    
    return wrapper


def require_json(func: Callable) -> Callable:
    """
    要求JSON请求装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
        return func(*args, **kwargs)
    
    return wrapper


def validate_form_data(validation_func: Callable) -> Callable:
    """
    表单数据验证装饰器
    
    Args:
        validation_func: 验证函数
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取表单数据
            form_data = request.form.to_dict()
            
            # 执行验证
            validation_result = validation_func(form_data)
            
            if not validation_result.is_valid:
                # 验证失败，显示错误信息
                for error in validation_result.get_errors():
                    flash(error, 'error')
                return None
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_result(timeout: int = 300) -> Callable:
    """
    结果缓存装饰器（简单的内存缓存）
    
    Args:
        timeout: 缓存超时时间（秒）
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            current_time = time.time()
            
            # 检查缓存
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if current_time - cached_time < timeout:
                    logging.debug(f"缓存命中: {func.__name__}")
                    return cached_result
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = (current_time, result)
            logging.debug(f"缓存存储: {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except DatabaseError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}")
                        time.sleep(delay)
                    else:
                        logging.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败")
                        raise last_exception
                except Exception as e:
                    # 非数据库错误不重试
                    raise e
            
            # 如果到这里，说明重试用尽
            raise last_exception
        
        return wrapper
    return decorator


def measure_performance(func: Callable) -> Callable:
    """
    性能测量装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = get_memory_usage()
            
            execution_time = end_time - start_time
            memory_diff = end_memory - start_memory
            
            logger = logging.getLogger(func.__module__)
            logger.info(f"性能统计 - 函数: {func.__name__}, "
                       f"执行时间: {execution_time:.3f}秒, "
                       f"内存变化: {memory_diff:.2f}MB")
    
    return wrapper


def get_memory_usage() -> float:
    """
    获取当前内存使用量（MB）
    
    Returns:
        内存使用量
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def validate_pagination(func: Callable) -> Callable:
    """
    分页参数验证装饰器
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 验证分页参数
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # 将验证后的参数添加到kwargs中
        kwargs['page'] = page
        kwargs['per_page'] = per_page
        
        return func(*args, **kwargs)
    
    return wrapper


def login_required(func: Callable) -> Callable:
    """
    Login required decorator - ensures user is authenticated

    Args:
        func: The function to decorate

    Returns:
        Decorated function that checks for authentication
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('main.login'))
        return func(*args, **kwargs)

    return wrapper


def role_required(*roles: str) -> Callable:
    """
    Role-based access control decorator

    Args:
        *roles: One or more roles that are allowed to access the decorated function
                Valid roles: 'technician', 'administrator'

    Returns:
        Decorator function

    Usage:
        @role_required('administrator')
        def admin_only_function():
            ...

        @role_required('technician', 'administrator')
        def staff_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is logged in
            if not session.get('logged_in'):
                flash('Please login to access this page', 'warning')
                return redirect(url_for('main.login'))

            # Check if user has required role
            user_role = session.get('user_type')
            if user_role not in roles:
                logging.warning(
                    f"Access denied: user role '{user_role}' not in {roles} "
                    f"for {func.__name__}"
                )
                flash('You do not have permission to access this page', 'error')
                abort(403)

            return func(*args, **kwargs)

        return wrapper
    return decorator


def admin_required(func: Callable) -> Callable:
    """
    Administrator permission decorator - shortcut for role_required('administrator')

    Args:
        func: The function to decorate

    Returns:
        Decorated function that checks for admin role
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is logged in
        if not session.get('logged_in'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('main.login'))

        # Check if user is an administrator
        user_role = session.get('user_type')
        if user_role != 'administrator':
            logging.warning(
                f"Admin access denied: user role '{user_role}' for {func.__name__}"
            )
            flash('Administrator permission required', 'error')
            abort(403)

        return func(*args, **kwargs)

    return wrapper


def technician_required(func: Callable) -> Callable:
    """
    Technician or higher permission decorator

    Args:
        func: The function to decorate

    Returns:
        Decorated function that checks for technician or admin role
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is logged in
        if not session.get('logged_in'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('main.login'))

        # Check if user is a technician or administrator
        user_role = session.get('user_type')
        if user_role not in ('technician', 'administrator'):
            logging.warning(
                f"Technician access denied: user role '{user_role}' for {func.__name__}"
            )
            flash('Technician permission required', 'error')
            abort(403)

        return func(*args, **kwargs)

    return wrapper 