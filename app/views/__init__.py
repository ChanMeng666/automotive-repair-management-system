"""
Views Module
Contains all routes and controller logic
"""
from .main import main_bp
from .technician import technician_bp
from .administrator import administrator_bp
from .auth import auth_bp

__all__ = ['main_bp', 'technician_bp', 'administrator_bp', 'auth_bp']
