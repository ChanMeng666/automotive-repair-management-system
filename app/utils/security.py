"""
安全管理模块
提供CSRF保护、密码哈希、输入验证、SQL注入防护等安全功能
"""
import secrets
import hashlib
import hmac
import re
import html
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
from flask import session, request, abort
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF令牌保护类"""
    
    @staticmethod
    def generate_token() -> str:
        """生成CSRF令牌"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """验证CSRF令牌"""
        if 'csrf_token' not in session:
            return False
        
        stored_token = session.get('csrf_token')
        if not stored_token or not token:
            return False
        
        # 使用恒定时间比较防止时序攻击
        return hmac.compare_digest(stored_token, token)
    
    @staticmethod
    def get_token() -> str:
        """获取当前CSRF令牌"""
        return session.get('csrf_token', '')


class PasswordSecurity:
    """密码安全管理类"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """使用PBKDF2哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        try:
            computed_hash, _ = PasswordSecurity.hash_password(password, salt)
            return hmac.compare_digest(stored_hash, computed_hash)
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False


class InputSanitizer:
    """输入数据清理和验证类"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """清理字符串输入"""
        if not isinstance(input_str, str):
            return ""
        
        cleaned = input_str.strip()
        
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        cleaned = html.escape(cleaned, quote=True)
        
        return cleaned
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        if not email or len(email) > 254:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证电话号码格式"""
        if not phone:
            return False
        
        cleaned_phone = re.sub(r'[^\d]', '', phone)
        
        if re.match(r'^1[3-9]\d{9}$', cleaned_phone):
            return True
        
        if re.match(r'^0\d{2,3}-?\d{7,8}$', phone):
            return True
        
        return False


class SQLInjectionProtection:
    """SQL注入防护类"""
    
    DANGEROUS_KEYWORDS = [
        'union', 'select', 'insert', 'update', 'delete', 'drop', 'create',
        'alter', 'exec', 'execute', '--', '/*', '*/', '1=1', 'or 1=1'
    ]
    
    @staticmethod
    def scan_sql_injection(input_str: str) -> bool:
        """扫描SQL注入攻击"""
        if not isinstance(input_str, str):
            return False
        
        lower_input = input_str.lower()
        
        for keyword in SQLInjectionProtection.DANGEROUS_KEYWORDS:
            if keyword in lower_input:
                logger.warning(f"检测到潜在SQL注入攻击: {keyword}")
                return True
        
        return False


class SessionSecurity:
    """会话安全管理类"""
    
    @staticmethod
    def generate_session_id() -> str:
        """生成安全的会话ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_session(user_id: str, ip_address: str) -> bool:
        """验证会话安全性"""
        if 'user_id' not in session:
            return False
        
        if session.get('user_id') != user_id:
            return False
        
        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_time > timedelta(hours=24):
                    return False
            except ValueError:
                return False
        
        return True
    
    @staticmethod
    def update_session_activity():
        """更新会话活动时间"""
        session['last_activity'] = datetime.now().isoformat()


# 装饰器函数
def csrf_protect(f):
    """CSRF保护装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            
            if not token or not CSRFProtection.validate_token(token):
                logger.warning(f"CSRF攻击尝试: {request.remote_addr}")
                abort(403, description="CSRF令牌无效")
        
        return f(*args, **kwargs)
    return decorated_function


def require_auth(user_types: List[str] = None):
    """认证要求装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                abort(401, description="需要登录访问")
            
            if user_types:
                user_type = session.get('user_type')
                if user_type not in user_types:
                    abort(403, description="权限不足")
            
            user_id = session.get('user_id')
            ip_address = request.remote_addr
            
            if not SessionSecurity.validate_session(user_id, ip_address):
                session.clear()
                abort(401, description="会话无效，请重新登录")
            
            SessionSecurity.update_session_activity()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 安全配置类
class SecurityConfig:
    """安全配置类"""
    
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    @classmethod
    def apply_security_headers(cls, response):
        """应用安全头"""
        for header, value in cls.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
