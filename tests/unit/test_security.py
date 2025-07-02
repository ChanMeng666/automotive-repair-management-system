"""
安全模块单元测试
测试CSRF保护、密码安全、输入验证、SQL注入防护等功能
"""
import pytest
from unittest.mock import Mock, patch
import secrets
import html

from app.utils.security import (
    CSRFProtection, PasswordSecurity, InputSanitizer, 
    SQLInjectionProtection, SessionSecurity, SecurityConfig,
    csrf_protect, require_auth
)


@pytest.mark.unit
@pytest.mark.security
class TestPasswordSecurity:
    """密码安全测试类"""
    
    def test_hash_password_generates_different_hashes(self):
        """测试相同密码生成不同哈希值"""
        password = "test123456"
        
        hash1, salt1 = PasswordSecurity.hash_password(password)
        hash2, salt2 = PasswordSecurity.hash_password(password)
        
        assert hash1 != hash2
        assert salt1 != salt2
        assert len(hash1) == 64  # SHA256哈希的十六进制长度
        assert len(salt1) == 32  # 16字节盐值的十六进制长度
    
    def test_hash_password_with_custom_salt(self):
        """测试使用自定义盐值的密码哈希"""
        password = "test123456"
        custom_salt = "custom_salt_value"
        
        hash1, salt1 = PasswordSecurity.hash_password(password, custom_salt)
        hash2, salt2 = PasswordSecurity.hash_password(password, custom_salt)
        
        assert hash1 == hash2  # 相同密码和盐值应产生相同哈希
        assert salt1 == salt2 == custom_salt
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "test123456"
        hash_value, salt = PasswordSecurity.hash_password(password)
        
        assert PasswordSecurity.verify_password(password, hash_value, salt) is True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "test123456"
        wrong_password = "wrong123456"
        hash_value, salt = PasswordSecurity.hash_password(password)
        
        assert PasswordSecurity.verify_password(wrong_password, hash_value, salt) is False
    
    def test_verify_password_exception_handling(self):
        """测试密码验证异常处理"""
        with patch('app.utils.security.PasswordSecurity.hash_password', side_effect=Exception("Test error")):
            result = PasswordSecurity.verify_password("test", "hash", "salt")
            assert result is False


@pytest.mark.unit
@pytest.mark.security
class TestInputSanitizer:
    """输入清理测试类"""
    
    def test_sanitize_string_basic(self):
        """测试基本字符串清理"""
        dirty_input = "  <script>alert('xss')</script>  "
        clean_output = InputSanitizer.sanitize_string(dirty_input)
        
        assert clean_output == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    
    def test_sanitize_string_max_length(self):
        """测试字符串长度限制"""
        long_input = "a" * 300
        clean_output = InputSanitizer.sanitize_string(long_input, max_length=100)
        
        assert len(clean_output) == 100
    
    def test_sanitize_string_non_string_input(self):
        """测试非字符串输入"""
        assert InputSanitizer.sanitize_string(123) == ""
        assert InputSanitizer.sanitize_string(None) == ""
        assert InputSanitizer.sanitize_string([]) == ""
    
    def test_validate_email_valid(self):
        """测试有效邮箱验证"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "firstname+lastname@company.org"
        ]
        
        for email in valid_emails:
            assert InputSanitizer.validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """测试无效邮箱验证"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            "a" * 250 + "@domain.com"  # 过长的邮箱
        ]
        
        for email in invalid_emails:
            assert InputSanitizer.validate_email(email) is False
    
    def test_validate_phone_valid_mobile(self):
        """测试有效手机号验证"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18699999999"
        ]
        
        for phone in valid_phones:
            assert InputSanitizer.validate_phone(phone) is True
    
    def test_validate_phone_valid_landline(self):
        """测试有效固话验证"""
        valid_landlines = [
            "010-12345678",
            "021-87654321",
            "0755-88888888"
        ]
        
        for phone in valid_landlines:
            assert InputSanitizer.validate_phone(phone) is True
    
    def test_validate_phone_invalid(self):
        """测试无效电话号码验证"""
        invalid_phones = [
            "12345",
            "abc123",
            "11112345678",  # 不是1开头的手机号
            "999999999999"  # 过长
        ]
        
        for phone in invalid_phones:
            assert InputSanitizer.validate_phone(phone) is False


@pytest.mark.unit
@pytest.mark.security
class TestSQLInjectionProtection:
    """SQL注入防护测试类"""
    
    def test_scan_safe_input(self):
        """测试安全输入"""
        safe_inputs = [
            "John Doe",
            "正常的中文内容",
            "123456",
            "user@example.com"
        ]
        
        for input_str in safe_inputs:
            assert SQLInjectionProtection.scan_sql_injection(input_str) is False
    
    def test_scan_dangerous_keywords(self):
        """测试危险关键词检测"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1 UNION SELECT * FROM users",
            "admin'--",
            "1 OR 1=1",
            "EXEC xp_cmdshell"
        ]
        
        for input_str in dangerous_inputs:
            assert SQLInjectionProtection.scan_sql_injection(input_str) is True
    
    def test_scan_non_string_input(self):
        """测试非字符串输入"""
        assert SQLInjectionProtection.scan_sql_injection(123) is False
        assert SQLInjectionProtection.scan_sql_injection(None) is False
        assert SQLInjectionProtection.scan_sql_injection([]) is False


@pytest.mark.unit
@pytest.mark.security
class TestCSRFProtection:
    """CSRF保护测试类"""
    
    def test_generate_token(self):
        """测试CSRF令牌生成"""
        with patch('flask.session', {}) as mock_session:
            token = CSRFProtection.generate_token()
            
            assert 'csrf_token' in mock_session
            assert len(token) > 20  # 令牌应该有合理的长度
            assert token == mock_session['csrf_token']
    
    def test_generate_token_existing(self):
        """测试已存在令牌的情况"""
        existing_token = "existing_token_123"
        with patch('flask.session', {'csrf_token': existing_token}) as mock_session:
            token = CSRFProtection.generate_token()
            
            assert token == existing_token
    
    def test_validate_token_valid(self):
        """测试有效令牌验证"""
        test_token = "valid_token_123"
        with patch('flask.session', {'csrf_token': test_token}):
            assert CSRFProtection.validate_token(test_token) is True
    
    def test_validate_token_invalid(self):
        """测试无效令牌验证"""
        with patch('flask.session', {'csrf_token': 'correct_token'}):
            assert CSRFProtection.validate_token('wrong_token') is False
            assert CSRFProtection.validate_token('') is False
            assert CSRFProtection.validate_token(None) is False
    
    def test_validate_token_no_session(self):
        """测试无会话令牌的情况"""
        with patch('flask.session', {}):
            assert CSRFProtection.validate_token('any_token') is False


@pytest.mark.unit
@pytest.mark.security
class TestSessionSecurity:
    """会话安全测试类"""
    
    def test_generate_session_id(self):
        """测试会话ID生成"""
        session_id1 = SessionSecurity.generate_session_id()
        session_id2 = SessionSecurity.generate_session_id()
        
        assert len(session_id1) > 20
        assert len(session_id2) > 20
        assert session_id1 != session_id2
    
    def test_validate_session_valid(self):
        """测试有效会话验证"""
        user_id = "test_user"
        ip_address = "192.168.1.1"
        
        mock_session = {
            'user_id': user_id,
            'last_activity': '2024-01-01T10:00:00'
        }
        
        with patch('flask.session', mock_session):
            # Mock datetime to simulate recent activity
            with patch('app.utils.security.datetime') as mock_datetime:
                from datetime import datetime, timedelta
                mock_datetime.now.return_value = datetime(2024, 1, 1, 11, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 10, 0, 0)
                
                assert SessionSecurity.validate_session(user_id, ip_address) is True
    
    def test_validate_session_invalid_user(self):
        """测试无效用户会话"""
        with patch('flask.session', {'user_id': 'different_user'}):
            assert SessionSecurity.validate_session('test_user', '192.168.1.1') is False
    
    def test_validate_session_no_session(self):
        """测试无会话"""
        with patch('flask.session', {}):
            assert SessionSecurity.validate_session('test_user', '192.168.1.1') is False


@pytest.mark.unit
@pytest.mark.security
class TestSecurityConfig:
    """安全配置测试类"""
    
    def test_apply_security_headers(self):
        """测试安全头部应用"""
        mock_response = Mock()
        mock_response.headers = {}
        
        result = SecurityConfig.apply_security_headers(mock_response)
        
        assert result == mock_response
        assert 'X-Content-Type-Options' in mock_response.headers
        assert 'X-Frame-Options' in mock_response.headers
        assert 'X-XSS-Protection' in mock_response.headers
        assert mock_response.headers['X-Content-Type-Options'] == 'nosniff'


@pytest.mark.unit
@pytest.mark.security
class TestSecurityDecorators:
    """安全装饰器测试类"""
    
    def test_csrf_protect_get_request(self):
        """测试GET请求不需要CSRF验证"""
        mock_func = Mock(return_value="success")
        
        with patch('flask.request') as mock_request:
            mock_request.method = 'GET'
            
            decorated_func = csrf_protect(mock_func)
            result = decorated_func()
            
            assert result == "success"
            mock_func.assert_called_once()
    
    def test_csrf_protect_post_valid_token(self):
        """测试POST请求有效CSRF令牌"""
        mock_func = Mock(return_value="success")
        
        with patch('flask.request') as mock_request, \
             patch('app.utils.security.CSRFProtection.validate_token', return_value=True):
            
            mock_request.method = 'POST'
            mock_request.form.get.return_value = 'valid_token'
            mock_request.headers.get.return_value = None
            
            decorated_func = csrf_protect(mock_func)
            result = decorated_func()
            
            assert result == "success"
            mock_func.assert_called_once()
    
    def test_csrf_protect_post_invalid_token(self):
        """测试POST请求无效CSRF令牌"""
        mock_func = Mock()
        
        with patch('flask.request') as mock_request, \
             patch('app.utils.security.CSRFProtection.validate_token', return_value=False), \
             patch('flask.abort') as mock_abort:
            
            mock_request.method = 'POST'
            mock_request.form.get.return_value = 'invalid_token'
            mock_request.headers.get.return_value = None
            mock_request.remote_addr = '127.0.0.1'
            
            decorated_func = csrf_protect(mock_func)
            decorated_func()
            
            mock_abort.assert_called_once_with(403, description="CSRF令牌无效")
            mock_func.assert_not_called()
    
    def test_require_auth_logged_in_user(self):
        """测试已登录用户访问"""
        mock_func = Mock(return_value="success")
        
        mock_session = {
            'logged_in': True,
            'user_type': 'technician',
            'user_id': 'test_user'
        }
        
        with patch('flask.session', mock_session), \
             patch('flask.request') as mock_request, \
             patch('app.utils.security.SessionSecurity.validate_session', return_value=True), \
             patch('app.utils.security.SessionSecurity.update_session_activity'):
            
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers.get.return_value = 'test-agent'
            
            decorated_func = require_auth()(mock_func)
            result = decorated_func()
            
            assert result == "success"
            mock_func.assert_called_once()
    
    def test_require_auth_not_logged_in(self):
        """测试未登录用户访问"""
        mock_func = Mock()
        
        with patch('flask.session', {}), \
             patch('flask.abort') as mock_abort:
            
            decorated_func = require_auth()(mock_func)
            decorated_func()
            
            mock_abort.assert_called_once_with(401, description="需要登录访问")
            mock_func.assert_not_called()
    
    def test_require_auth_insufficient_permissions(self):
        """测试权限不足"""
        mock_func = Mock()
        
        mock_session = {
            'logged_in': True,
            'user_type': 'technician'
        }
        
        with patch('flask.session', mock_session), \
             patch('flask.abort') as mock_abort:
            
            decorated_func = require_auth(['administrator'])(mock_func)
            decorated_func()
            
            mock_abort.assert_called_once_with(403, description="权限不足")
            mock_func.assert_not_called() 