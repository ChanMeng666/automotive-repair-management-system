"""
错误处理和日志系统模块
提供统一的错误处理、异常记录、审计日志等功能
"""
import logging
import logging.handlers
import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from flask import Flask, request, session, jsonify, render_template
from werkzeug.exceptions import HTTPException
import os


class LoggerConfig:
    """日志配置类"""
    
    # 日志级别映射
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    @staticmethod
    def setup_logging(app: Flask):
        """设置应用日志系统"""
        log_dir = Path(app.config.get('LOG_DIR', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        # 获取日志级别
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        level = LoggerConfig.LOG_LEVELS.get(log_level, logging.INFO)
        
        # 创建根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 应用日志文件处理器
        app_log_file = log_dir / 'app.log'
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(level)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)
        
        # 错误日志文件处理器
        error_log_file = log_dir / 'error.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        app.logger.info("日志系统初始化完成")


class ApplicationError(Exception):
    """自定义应用错误基类"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ValidationError(ApplicationError):
    """验证错误"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message, 'VALIDATION_ERROR', 400)
        self.field = field


class BusinessLogicError(ApplicationError):
    """业务逻辑错误"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'BUSINESS_ERROR', 422)


class SecurityError(ApplicationError):
    """安全错误"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'SECURITY_ERROR', 403)


class DatabaseError(ApplicationError):
    """数据库错误"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'DATABASE_ERROR', 500)


class ErrorHandler:
    """错误处理器类"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化错误处理器"""
        self.app = app
        
        # 注册错误处理器
        app.errorhandler(404)(self.handle_404)
        app.errorhandler(403)(self.handle_403)
        app.errorhandler(401)(self.handle_401)
        app.errorhandler(500)(self.handle_500)
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(BusinessLogicError)(self.handle_business_error)
        app.errorhandler(SecurityError)(self.handle_security_error)
        app.errorhandler(DatabaseError)(self.handle_database_error)
    
    def handle_404(self, error):
        """处理404错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Resource not found',
                'message': '请求的资源不存在',
                'status_code': 404
            }), 404
        
        return render_template('errors/404.html'), 404
    
    def handle_403(self, error):
        """处理403错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Access forbidden',
                'message': '访问被拒绝',
                'status_code': 403
            }), 403
        
        return render_template('errors/403.html'), 403
    
    def handle_401(self, error):
        """处理401错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': '需要登录访问',
                'status_code': 401
            }), 401
        
        return render_template('auth/login.html'), 401
    
    def handle_500(self, error):
        """处理500错误"""
        self.app.logger.error(f"服务器内部错误: {error}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': '服务器内部错误',
                'status_code': 500
            }), 500
        
        return render_template('errors/500.html'), 500
    
    def handle_validation_error(self, error: ValidationError):
        """处理验证错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Validation error',
                'message': error.message,
                'field': error.field,
                'status_code': error.status_code
            }), error.status_code
        
        return render_template('errors/404.html'), error.status_code
    
    def handle_business_error(self, error: BusinessLogicError):
        """处理业务逻辑错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Business logic error',
                'message': error.message,
                'error_code': error.error_code,
                'status_code': error.status_code
            }), error.status_code
        
        return render_template('errors/500.html'), error.status_code
    
    def handle_security_error(self, error: SecurityError):
        """处理安全错误"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Security error',
                'message': error.message,
                'status_code': error.status_code
            }), error.status_code
        
        return render_template('errors/403.html'), error.status_code
    
    def handle_database_error(self, error: DatabaseError):
        """处理数据库错误"""
        self.app.logger.error(f"数据库错误: {error.message}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Database error',
                'message': '数据库操作失败',
                'status_code': error.status_code
            }), error.status_code
        
        return render_template('errors/500.html'), error.status_code
