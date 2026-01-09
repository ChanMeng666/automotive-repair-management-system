"""
配置管理系统
"""
import os
from datetime import timedelta


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


class BaseConfig:
    """基础配置类"""
    # 安全配置 - 从环境变量读取，开发环境允许默认值
    SECRET_KEY = os.environ.get('SECRET_KEY')

    @classmethod
    def validate_config(cls):
        """验证必要的配置项"""
        pass  # 基础配置不强制验证
    
    # 数据库配置
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'spb')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Flask配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    JSON_AS_ASCII = False
    
    # 会话安全配置
    SESSION_COOKIE_SECURE = False  # 开发环境设为False，生产环境应为True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 分页配置
    ITEMS_PER_PAGE = 10
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

    # 开发环境使用默认密钥（仅用于本地开发）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-secret-key-not-for-production'

    @classmethod
    def validate_config(cls):
        """开发环境配置验证"""
        import logging
        if not os.environ.get('SECRET_KEY'):
            logging.warning(
                "WARNING: SECRET_KEY not set in environment. "
                "Using development default. DO NOT use in production!"
            )


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True  # 生产环境必须启用HTTPS

    @classmethod
    def validate_config(cls):
        """生产环境配置验证 - 强制要求必要配置"""
        errors = []

        if not os.environ.get('SECRET_KEY'):
            errors.append("SECRET_KEY environment variable is required in production")

        if not os.environ.get('DB_PASSWORD'):
            errors.append("DB_PASSWORD environment variable is required in production")

        if errors:
            raise ConfigurationError(
                "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)

        # 生产环境特定配置
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    DB_NAME = 'spb_test'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name):
    """获取配置类"""
    return config.get(config_name, config['default']) 