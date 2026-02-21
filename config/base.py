"""
Configuration Management System
Supports DATABASE_URL for cloud databases (Neon, Heroku)
Includes Neon Auth configuration for JWT authentication
"""
import os
from datetime import timedelta


class ConfigurationError(Exception):
    """Configuration error exception"""
    pass


class BaseConfig:
    """Base configuration class"""

    # Security configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')

    @classmethod
    def validate_config(cls):
        """Validate required configuration items"""
        pass

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # Individual database variables (fallback)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 5432))
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'spb')

    # SSL mode for cloud databases
    DB_SSLMODE = os.environ.get('DB_SSLMODE', 'require')

    # Neon Auth configuration (powered by Better Auth)
    # Auth URL format: https://ep-xxx.neonauth.xxx.aws.neon.tech/dbname/auth
    NEON_AUTH_URL = os.environ.get('NEON_AUTH_URL')
    NEON_AUTH_JWKS_URL = os.environ.get('NEON_AUTH_JWKS_URL')
    NEON_AUTH_ENABLED = bool(os.environ.get('NEON_AUTH_URL'))

    # Flask configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    JSON_AS_ASCII = False

    # Session security
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Pagination
    ITEMS_PER_PAGE = 10

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        pass


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-secret-key-not-for-production'
    DB_SSLMODE = os.environ.get('DB_SSLMODE', 'prefer')

    @classmethod
    def validate_config(cls):
        """Development configuration validation"""
        import logging
        if not os.environ.get('SECRET_KEY'):
            logging.warning(
                "WARNING: SECRET_KEY not set. Using development default. "
                "DO NOT use in production!"
            )


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'

    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    DB_SSLMODE = os.environ.get('DB_SSLMODE', 'require')

    @classmethod
    def validate_config(cls):
        """Production configuration validation"""
        errors = []

        if not os.environ.get('SECRET_KEY'):
            errors.append("SECRET_KEY environment variable is required in production")

        if not os.environ.get('DATABASE_URL') and not os.environ.get('DB_PASSWORD'):
            errors.append("DATABASE_URL or DB_PASSWORD is required in production")

        if errors:
            raise ConfigurationError(
                "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)

        import logging

        # Use stdout logging for cloud platforms
        if os.environ.get('LOG_TO_STDOUT'):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
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
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    DB_NAME = 'spb_test'
    SECRET_KEY = 'testing-secret-key'
    DB_SSLMODE = os.environ.get('DB_SSLMODE', 'disable')

    # Use SQLite for tests if no DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///:memory:'
    )


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name):
    """Get configuration class"""
    return config.get(config_name, config['default'])
