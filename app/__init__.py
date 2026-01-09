"""
Automotive Repair Management System
Flask应用工厂和应用初始化
"""
from flask import Flask
from config.base import get_config
from app.utils.error_handler import ErrorHandler, LoggerConfig
from app.utils.security import SecurityConfig, CSRFProtection
import os


def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)

    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    config = get_config(config_name)
    app.config.from_object(config)

    # 验证配置
    if hasattr(config, 'validate_config'):
        config.validate_config()

    # 确保密钥已设置
    if not app.config.get('SECRET_KEY'):
        if config_name == 'production':
            raise ValueError("SECRET_KEY must be set in production environment")
        # 开发环境使用配置类中的默认值
        app.config['SECRET_KEY'] = getattr(config, 'SECRET_KEY', None)
        if not app.config['SECRET_KEY']:
            raise ValueError("SECRET_KEY is required")
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册安全中间件
    register_security_middleware(app)
    
    app.logger.info("应用初始化完成")
    
    return app


def init_extensions(app):
    """初始化Flask扩展"""
    # 设置日志系统
    LoggerConfig.setup_logging(app)
    
    # 根据环境选择数据库连接方式
    if app.config.get('ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production':
        # 生产环境使用PythonAnywhere优化的数据库连接
        from app.utils.database_pythonanywhere import init_database
        init_database(app)
    else:
        # 开发环境使用标准数据库连接
        from app.utils.database import init_database
        init_database(app)
    
    # 初始化错误处理器
    error_handler = ErrorHandler(app)


def register_blueprints(app):
    """注册蓝图"""
    from app.views.main import main_bp
    from app.views.technician import technician_bp
    from app.views.administrator import administrator_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(technician_bp, url_prefix='/technician')
    app.register_blueprint(administrator_bp, url_prefix='/administrator')


def register_error_handlers(app):
    """注册错误处理器"""
    # ErrorHandler已在init_extensions中初始化，这里保留为向后兼容
    pass


def register_security_middleware(app):
    """注册安全中间件"""
    
    @app.after_request
    def apply_security_headers(response):
        return SecurityConfig.apply_security_headers(response)
    
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': CSRFProtection.generate_token} 