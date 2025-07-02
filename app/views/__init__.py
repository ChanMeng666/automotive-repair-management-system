"""
视图层模块
包含所有的路由和控制器逻辑
"""
from .main import main_bp
from .technician import technician_bp
from .administrator import administrator_bp

__all__ = ['main_bp', 'technician_bp', 'administrator_bp'] 