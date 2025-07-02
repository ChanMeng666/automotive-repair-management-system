"""
测试工具模块
提供通用的测试辅助函数和工具
"""
import json
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock


def create_mock_customer(customer_id: int = 1, **kwargs) -> Mock:
    """创建模拟客户对象"""
    default_data = {
        'customer_id': customer_id,
        'first_name': '张',
        'last_name': '三',
        'full_name': '张三',
        'email': f'customer{customer_id}@example.com',
        'phone': '13812345678',
        'address': '北京市朝阳区测试街道123号',
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }
    default_data.update(kwargs)
    
    mock_customer = Mock()
    for key, value in default_data.items():
        setattr(mock_customer, key, value)
    
    return mock_customer


def create_mock_job(job_id: int = 1, customer_id: int = 1, **kwargs) -> Mock:
    """创建模拟工作订单对象"""
    default_data = {
        'job_id': job_id,
        'customer_id': customer_id,
        'vehicle_info': '2020年丰田凯美瑞',
        'problem_description': '发动机异响',
        'status': '进行中',
        'total_cost': 1500.00,
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-01 10:00:00'
    }
    default_data.update(kwargs)
    
    mock_job = Mock()
    for key, value in default_data.items():
        setattr(mock_job, key, value)
    
    return mock_job


def create_mock_service(service_id: int = 1, **kwargs) -> Mock:
    """创建模拟服务对象"""
    default_data = {
        'service_id': service_id,
        'service_name': '发动机检修',
        'description': '检查和维修发动机问题',
        'base_price': 800.00,
        'estimated_hours': 4.0
    }
    default_data.update(kwargs)
    
    mock_service = Mock()
    for key, value in default_data.items():
        setattr(mock_service, key, value)
    
    return mock_service


def create_mock_part(part_id: int = 1, **kwargs) -> Mock:
    """创建模拟零件对象"""
    default_data = {
        'part_id': part_id,
        'part_name': '机油滤清器',
        'part_number': 'OF-001',
        'price': 45.00,
        'supplier': '丰田原厂',
        'stock_quantity': 50
    }
    default_data.update(kwargs)
    
    mock_part = Mock()
    for key, value in default_data.items():
        setattr(mock_part, key, value)
    
    return mock_part


def assert_json_response(response, expected_status: int = 200, expected_keys: Optional[list] = None):
    """断言JSON响应"""
    assert response.status_code == expected_status
    assert response.content_type == 'application/json'
    
    data = json.loads(response.data)
    
    if expected_keys:
        for key in expected_keys:
            assert key in data
    
    return data


def assert_redirect_response(response, expected_location: str = None):
    """断言重定向响应"""
    assert response.status_code in [301, 302, 303, 307, 308]
    
    if expected_location:
        assert expected_location in response.location
    
    return response.location


def create_test_form_data(base_data: Dict[str, Any], csrf_token: str = 'test_token') -> Dict[str, Any]:
    """创建测试表单数据"""
    form_data = base_data.copy()
    form_data['csrf_token'] = csrf_token
    return form_data


class MockDatabaseCursor:
    """模拟数据库游标"""
    
    def __init__(self, fetch_data: Any = None, rowcount: int = 0):
        self.fetch_data = fetch_data
        self.rowcount = rowcount
        self.executed_queries = []
    
    def execute(self, query: str, params: tuple = None):
        """模拟执行查询"""
        self.executed_queries.append((query, params))
    
    def fetchone(self):
        """模拟获取一行数据"""
        return self.fetch_data if not isinstance(self.fetch_data, list) else (
            self.fetch_data[0] if self.fetch_data else None
        )
    
    def fetchall(self):
        """模拟获取所有数据"""
        return self.fetch_data if isinstance(self.fetch_data, list) else (
            [self.fetch_data] if self.fetch_data else []
        )
    
    def close(self):
        """模拟关闭游标"""
        pass


class MockDatabaseConnection:
    """模拟数据库连接"""
    
    def __init__(self, cursor_data: Any = None, cursor_rowcount: int = 0):
        self.cursor_data = cursor_data
        self.cursor_rowcount = cursor_rowcount
        self.committed = False
        self.rolled_back = False
    
    def cursor(self, dictionary=True, buffered=True):
        """模拟创建游标"""
        return MockDatabaseCursor(self.cursor_data, self.cursor_rowcount)
    
    def commit(self):
        """模拟提交事务"""
        self.committed = True
    
    def rollback(self):
        """模拟回滚事务"""
        self.rolled_back = True
    
    def close(self):
        """模拟关闭连接"""
        pass


def create_mock_db_manager(return_data: Any = None, rowcount: int = 0):
    """创建模拟数据库管理器"""
    mock_manager = Mock()
    mock_connection = MockDatabaseConnection(return_data, rowcount)
    
    mock_manager.get_connection.return_value = mock_connection
    mock_manager.get_cursor.return_value.__enter__.return_value = mock_connection.cursor()
    mock_manager.get_cursor.return_value.__exit__.return_value = None
    mock_manager.transaction.return_value.__enter__.return_value = mock_connection.cursor()
    mock_manager.transaction.return_value.__exit__.return_value = None
    
    return mock_manager


def generate_test_data_set(count: int, data_type: str = 'customer') -> list:
    """生成测试数据集"""
    data_generators = {
        'customer': lambda i: {
            'customer_id': i,
            'first_name': f'客户{i}',
            'last_name': '测试',
            'full_name': f'客户{i}测试',
            'email': f'customer{i}@test.com',
            'phone': f'138{i:08d}',
            'address': f'测试地址{i}号'
        },
        'job': lambda i: {
            'job_id': i,
            'customer_id': (i - 1) % 10 + 1,  # 循环关联客户
            'vehicle_info': f'测试车辆{i}',
            'problem_description': f'问题描述{i}',
            'status': ['等待中', '进行中', '已完成'][i % 3],
            'total_cost': 100.0 * i
        },
        'service': lambda i: {
            'service_id': i,
            'service_name': f'服务{i}',
            'description': f'服务描述{i}',
            'base_price': 50.0 * i,
            'estimated_hours': i % 8 + 1
        },
        'part': lambda i: {
            'part_id': i,
            'part_name': f'零件{i}',
            'part_number': f'P{i:03d}',
            'price': 10.0 * i,
            'supplier': f'供应商{i}',
            'stock_quantity': i * 10
        }
    }
    
    generator = data_generators.get(data_type)
    if not generator:
        raise ValueError(f"不支持的数据类型: {data_type}")
    
    return [generator(i) for i in range(1, count + 1)]


class TestResponseHelper:
    """测试响应辅助类"""
    
    @staticmethod
    def assert_success_response(response, expected_message: str = None):
        """断言成功响应"""
        assert response.status_code == 200
        if expected_message:
            assert expected_message.encode('utf-8') in response.data
    
    @staticmethod
    def assert_error_response(response, expected_status: int = 400, expected_message: str = None):
        """断言错误响应"""
        assert response.status_code == expected_status
        if expected_message:
            assert expected_message.encode('utf-8') in response.data
    
    @staticmethod
    def assert_api_success(response, expected_data_keys: list = None):
        """断言API成功响应"""
        data = assert_json_response(response, 200)
        if expected_data_keys:
            for key in expected_data_keys:
                assert key in data
        return data
    
    @staticmethod
    def assert_api_error(response, expected_status: int = 400, expected_error_key: str = 'error'):
        """断言API错误响应"""
        data = assert_json_response(response, expected_status)
        assert expected_error_key in data
        return data


def mock_security_decorators():
    """模拟安全装饰器，在测试中禁用安全检查"""
    def csrf_protect_mock(f):
        return f
    
    def require_auth_mock(*args, **kwargs):
        def decorator(f):
            return f
        return decorator
    
    return csrf_protect_mock, require_auth_mock 