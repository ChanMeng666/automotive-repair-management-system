"""
pytest配置文件
定义测试夹具(fixtures)和全局测试配置
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from flask import Flask

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.base import TestingConfig


@pytest.fixture(scope='session')
def app():
    """创建测试用Flask应用实例"""
    app = create_app('testing')
    app.config.from_object(TestingConfig)
    
    # 测试环境特定配置
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # 在测试中禁用CSRF
        'SECRET_KEY': 'test-secret-key',
        'DB_NAME': 'spb_test',
        'LOG_LEVEL': 'ERROR'  # 减少测试时的日志输出
    })
    
    return app


@pytest.fixture(scope='session')
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def mock_db_cursor():
    """模拟数据库游标"""
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.rowcount = 0
    return mock_cursor


@pytest.fixture
def mock_db_connection():
    """模拟数据库连接"""
    mock_conn = Mock()
    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_db_cursor())
    mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    return mock_conn


@pytest.fixture
def mock_db_manager(mock_db_connection):
    """模拟数据库管理器"""
    with patch('app.utils.database.db_manager') as mock_manager:
        mock_manager.get_connection.return_value = mock_db_connection
        mock_manager.get_cursor.return_value.__enter__ = Mock(return_value=mock_db_cursor())
        mock_manager.get_cursor.return_value.__exit__ = Mock(return_value=None)
        yield mock_manager


@pytest.fixture
def sample_customer_data():
    """示例客户数据"""
    return {
        'customer_id': 1,
        'first_name': '张',
        'last_name': '三',
        'full_name': '张三',
        'email': 'zhangsan@example.com',
        'phone': '13812345678',
        'address': '北京市朝阳区测试街道123号',
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }


@pytest.fixture
def sample_job_data():
    """示例工作订单数据"""
    return {
        'job_id': 1,
        'customer_id': 1,
        'vehicle_info': '2020年丰田凯美瑞',
        'problem_description': '发动机异响',
        'status': '进行中',
        'total_cost': 1500.00,
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }


@pytest.fixture
def sample_service_data():
    """示例服务数据"""
    return {
        'service_id': 1,
        'service_name': '发动机检修',
        'description': '检查和维修发动机问题',
        'base_price': 800.00,
        'estimated_hours': 4.0
    }


@pytest.fixture
def sample_part_data():
    """示例零件数据"""
    return {
        'part_id': 1,
        'part_name': '机油滤清器',
        'part_number': 'OF-001',
        'price': 45.00,
        'supplier': '丰田原厂',
        'stock_quantity': 50
    }


@pytest.fixture
def authenticated_session(client):
    """已认证的会话"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
        sess['user_type'] = 'technician'
        sess['logged_in'] = True
    return client


@pytest.fixture
def admin_session(client):
    """管理员会话"""
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin_user'
        sess['user_type'] = 'administrator'
        sess['logged_in'] = True
    return client


# 测试标记
pytest_plugins = []

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "unit: 标记为单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试"
    )
    config.addinivalue_line(
        "markers", "security: 标记为安全测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    ) 