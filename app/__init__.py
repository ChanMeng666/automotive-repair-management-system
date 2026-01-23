"""
Automotive Repair Management System
Flask Application Factory and Initialization
"""
from flask import Flask
from config.base import get_config
from app.extensions import db
from app.utils.error_handler import ErrorHandler, LoggerConfig
from app.utils.security import SecurityConfig, CSRFProtection
import os


def create_app(config_name=None):
    """Application Factory Function"""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    config = get_config(config_name)
    app.config.from_object(config)

    # Validate configuration
    if hasattr(config, 'validate_config'):
        config.validate_config()

    # Ensure secret key is set
    if not app.config.get('SECRET_KEY'):
        if config_name == 'production':
            raise ValueError("SECRET_KEY must be set in production environment")
        app.config['SECRET_KEY'] = getattr(config, 'SECRET_KEY', None)
        if not app.config['SECRET_KEY']:
            raise ValueError("SECRET_KEY is required")

    # Configure SQLAlchemy database URI
    _configure_database(app, config)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register security middleware
    register_security_middleware(app)

    app.logger.info("Application initialization complete")

    return app


def _configure_database(app, config):
    """Configure SQLAlchemy database URI"""
    # Check for DATABASE_URL first (Neon, Heroku, etc.)
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Handle Heroku's postgres:// vs postgresql:// issue
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Build URI from individual components
        db_user = config.DB_USER
        db_password = config.DB_PASSWORD
        db_host = config.DB_HOST
        db_port = config.DB_PORT
        db_name = config.DB_NAME

        # Build PostgreSQL URI
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )

    # SQLAlchemy configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = app.config.get('DEBUG', False)

    # Connection pool settings for Neon/cloud databases
    sslmode = getattr(config, 'DB_SSLMODE', 'require')
    if sslmode and sslmode != 'disable':
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'sslmode': sslmode},
            'pool_pre_ping': True,  # Verify connections before use
            'pool_size': 5,
            'max_overflow': 10,
            'pool_recycle': 300,  # Recycle connections every 5 minutes
        }


def init_extensions(app):
    """Initialize Flask extensions"""
    # Setup logging system
    LoggerConfig.setup_logging(app)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Create tables in development (in production, use migrations)
    with app.app_context():
        # Import models to register with SQLAlchemy
        from app.models import Customer, Job, JobService, JobPart, Service, Part, User

        if app.config.get('ENV') != 'production':
            db.create_all()

    # Initialize OAuth
    from app.services.oauth_service import init_oauth
    init_oauth(app)

    # Initialize error handler
    ErrorHandler(app)


def register_blueprints(app):
    """Register blueprints"""
    from app.views.main import main_bp
    from app.views.technician import technician_bp
    from app.views.administrator import administrator_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(technician_bp, url_prefix='/technician')
    app.register_blueprint(administrator_bp, url_prefix='/administrator')

    # Register auth blueprint if it exists
    try:
        from app.views.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError:
        pass  # Auth blueprint not yet created


def register_error_handlers(app):
    """Register error handlers"""
    pass


def register_security_middleware(app):
    """Register security middleware"""

    @app.after_request
    def apply_security_headers(response):
        return SecurityConfig.apply_security_headers(response)

    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': CSRFProtection.generate_token}
