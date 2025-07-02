"""
基础测试
验证测试框架和基本功能
"""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestBasicFunctionality:
    """基础功能测试类"""
    
    def test_basic_assertion(self):
        """测试基本断言"""
        assert 1 + 1 == 2
        assert "hello" == "hello"
        assert [1, 2, 3] == [1, 2, 3]
    
    def test_mock_functionality(self):
        """测试Mock功能"""
        mock_obj = Mock()
        mock_obj.test_method.return_value = "test_result"
        
        result = mock_obj.test_method()
        assert result == "test_result"
        mock_obj.test_method.assert_called_once()
    
    def test_patch_functionality(self):
        """测试patch功能"""
        with patch('builtins.len', return_value=10):
            assert len([1, 2, 3]) == 10
    
    def test_pytest_markers(self):
        """测试pytest标记"""
        # 这个测试本身就标记为unit测试
        assert True


@pytest.mark.unit
class TestImports:
    """导入测试类"""
    
    def test_import_app(self):
        """测试应用模块导入"""
        try:
            from app import create_app
            assert create_app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import create_app: {e}")
    
    def test_import_config(self):
        """测试配置模块导入"""
        try:
            from config.base import Config, DevelopmentConfig, ProductionConfig, TestingConfig
            assert Config is not None
            assert DevelopmentConfig is not None
            assert ProductionConfig is not None
            assert TestingConfig is not None
        except ImportError as e:
            pytest.fail(f"Failed to import config classes: {e}")
    
    def test_import_utils(self):
        """测试工具模块导入"""
        try:
            from app.utils.database import DatabaseManager
            from app.utils.validators import DataValidator
            from app.utils.security import PasswordSecurity, InputSanitizer
            assert DatabaseManager is not None
            assert DataValidator is not None
            assert PasswordSecurity is not None
            assert InputSanitizer is not None
        except ImportError as e:
            pytest.fail(f"Failed to import utility classes: {e}")


@pytest.mark.unit
class TestUtilityFunctions:
    """工具函数测试类"""
    
    def test_password_hashing(self):
        """测试密码哈希功能"""
        from app.utils.security import PasswordSecurity
        
        password = "test123456"
        hash_value, salt = PasswordSecurity.hash_password(password)
        
        assert hash_value is not None
        assert salt is not None
        assert len(hash_value) == 64  # SHA256哈希长度
        assert len(salt) == 32  # 16字节盐值的十六进制长度
        
        # 验证正确密码
        assert PasswordSecurity.verify_password(password, hash_value, salt) is True
        
        # 验证错误密码
        assert PasswordSecurity.verify_password("wrong_password", hash_value, salt) is False
    
    def test_input_sanitization(self):
        """测试输入清理功能"""
        from app.utils.security import InputSanitizer
        
        # 测试HTML转义
        dirty_input = "<script>alert('xss')</script>"
        clean_output = InputSanitizer.sanitize_string(dirty_input)
        assert "<script>" not in clean_output
        assert "&lt;script&gt;" in clean_output
        
        # 测试邮箱验证
        assert InputSanitizer.validate_email("test@example.com") is True
        assert InputSanitizer.validate_email("invalid-email") is False
        
        # 测试手机号验证
        assert InputSanitizer.validate_phone("13812345678") is True
        assert InputSanitizer.validate_phone("invalid-phone") is False
    
    def test_sql_injection_detection(self):
        """测试SQL注入检测"""
        from app.utils.security import SQLInjectionProtection
        
        # 安全输入
        assert SQLInjectionProtection.scan_sql_injection("normal text") is False
        assert SQLInjectionProtection.scan_sql_injection("user@example.com") is False
        
        # 危险输入
        assert SQLInjectionProtection.scan_sql_injection("'; DROP TABLE users; --") is True
        assert SQLInjectionProtection.scan_sql_injection("1 UNION SELECT") is True
    
    def test_data_validation(self):
        """测试数据验证功能"""
        from app.utils.validators import DataValidator
        
        # 测试必填字段验证
        data = {"name": "test", "email": "test@example.com"}
        required_fields = ["name", "email"]
        
        is_valid, errors = DataValidator.validate_required_fields(data, required_fields)
        assert is_valid is True
        assert len(errors) == 0
        
        # 测试缺少必填字段
        incomplete_data = {"name": "test"}
        is_valid, errors = DataValidator.validate_required_fields(incomplete_data, required_fields)
        assert is_valid is False
        assert len(errors) > 0


@pytest.mark.integration
class TestApplicationIntegration:
    """应用集成测试类"""
    
    def test_create_app(self):
        """测试应用创建"""
        from app import create_app
        
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_database_manager_init(self):
        """测试数据库管理器初始化"""
        from app.utils.database import DatabaseManager
        
        # 创建一个测试配置的数据库管理器
        config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }
        
        db_manager = DatabaseManager(config)
        assert db_manager is not None
        assert db_manager.config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 