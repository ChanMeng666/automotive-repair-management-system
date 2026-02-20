"""
Error Handling and Logging System Module
Provides unified error handling, exception logging, and audit logging functionality
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
    """Logger configuration"""

    # Log level mapping
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    @staticmethod
    def setup_logging(app: Flask):
        """Set up the application logging system"""
        log_dir = Path(app.config.get('LOG_DIR', 'logs'))
        log_dir.mkdir(exist_ok=True)

        # Get log level
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        level = LoggerConfig.LOG_LEVELS.get(log_level, logging.INFO)

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Application log file handler
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

        # Error log file handler
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

        app.logger.info("Logging system initialized")


class ApplicationError(Exception):
    """Custom application error base class"""

    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ValidationError(ApplicationError):
    """Validation error"""

    def __init__(self, message: str, field: str = None):
        super().__init__(message, 'VALIDATION_ERROR', 400)
        self.field = field


class BusinessLogicError(ApplicationError):
    """Business logic error"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'BUSINESS_ERROR', 422)


class SecurityError(ApplicationError):
    """Security error"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'SECURITY_ERROR', 403)


class DatabaseError(ApplicationError):
    """Database error"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'DATABASE_ERROR', 500)


class ErrorHandler:
    """Error handler"""

    def __init__(self, app: Flask = None):
        self.app = app

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the error handler"""
        self.app = app

        # Register error handlers
        app.errorhandler(404)(self.handle_404)
        app.errorhandler(403)(self.handle_403)
        app.errorhandler(401)(self.handle_401)
        app.errorhandler(500)(self.handle_500)
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(BusinessLogicError)(self.handle_business_error)
        app.errorhandler(SecurityError)(self.handle_security_error)
        app.errorhandler(DatabaseError)(self.handle_database_error)

    def handle_404(self, error):
        """Handle 404 error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Resource not found',
                'message': 'The requested resource does not exist',
                'status_code': 404
            }), 404

        return render_template('errors/404.html'), 404

    def handle_403(self, error):
        """Handle 403 error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Access forbidden',
                'message': 'Access denied',
                'status_code': 403
            }), 403

        return render_template('errors/403.html'), 403

    def handle_401(self, error):
        """Handle 401 error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Login required',
                'status_code': 401
            }), 401

        return render_template('auth/login.html'), 401

    def handle_500(self, error):
        """Handle 500 error"""
        self.app.logger.error(f"Internal server error: {error}")

        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An internal server error occurred',
                'status_code': 500
            }), 500

        return render_template('errors/500.html'), 500

    def handle_validation_error(self, error: ValidationError):
        """Handle validation error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Validation error',
                'message': error.message,
                'field': error.field,
                'status_code': error.status_code
            }), error.status_code

        return render_template('errors/404.html'), error.status_code

    def handle_business_error(self, error: BusinessLogicError):
        """Handle business logic error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Business logic error',
                'message': error.message,
                'error_code': error.error_code,
                'status_code': error.status_code
            }), error.status_code

        return render_template('errors/500.html'), error.status_code

    def handle_security_error(self, error: SecurityError):
        """Handle security error"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Security error',
                'message': error.message,
                'status_code': error.status_code
            }), error.status_code

        return render_template('errors/403.html'), error.status_code

    def handle_database_error(self, error: DatabaseError):
        """Handle database error"""
        self.app.logger.error(f"Database error: {error.message}")

        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Database error',
                'message': 'Database operation failed',
                'status_code': error.status_code
            }), error.status_code

        return render_template('errors/500.html'), error.status_code
