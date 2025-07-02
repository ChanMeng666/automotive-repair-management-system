"""
配置模块初始化
"""
from .base import get_config, BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig

__all__ = ['get_config', 'BaseConfig', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig'] 