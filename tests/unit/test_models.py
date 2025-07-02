"""
模型层单元测试
测试Customer、Job、Service、Part等模型的业务逻辑
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from app.models.customer import Customer
from app.models.job import Job
from app.models.service import Service
from app.models.part import Part


@pytest.mark.unit
class TestCustomerModel:
    """客户模型测试类"""
    
    def test_customer_init(self, sample_customer_data):
        """测试客户模型初始化"""
        customer = Customer(**sample_customer_data)
        
        assert customer.customer_id == sample_customer_data['customer_id']
        assert customer.first_name == sample_customer_data['first_name']
        assert customer.last_name == sample_customer_data['last_name']
        assert customer.full_name == sample_customer_data['full_name']
        assert customer.email == sample_customer_data['email']
        assert customer.phone == sample_customer_data['phone']
        assert customer.address == sample_customer_data['address']
    
    @patch('app.models.customer.execute_query')
    def test_get_by_id_found(self, mock_execute_query, sample_customer_data):
        """测试根据ID获取客户 - 找到客户"""
        mock_execute_query.return_value = sample_customer_data
        
        customer = Customer.get_by_id(1)
        
        assert customer is not None
        assert customer.customer_id == 1
        assert customer.full_name == '张三'
        mock_execute_query.assert_called_once()
    
    @patch('app.models.customer.execute_query')
    def test_get_by_id_not_found(self, mock_execute_query):
        """测试根据ID获取客户 - 未找到客户"""
        mock_execute_query.return_value = None
        
        customer = Customer.get_by_id(999)
        
        assert customer is None
        mock_execute_query.assert_called_once()
    
    def test_validate_customer_data_valid(self):
        """测试有效客户数据验证"""
        valid_data = {
            'first_name': '王',
            'last_name': '五',
            'email': 'wangwu@example.com',
            'phone': '13812345678',
            'address': '广州市天河区测试街789号'
        }
        
        is_valid, errors = Customer.validate_customer_data(valid_data)
        
        assert is_valid is True
        assert len(errors) == 0