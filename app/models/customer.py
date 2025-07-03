"""
Customer model
"""
from typing import List, Optional, Dict, Any
from .base import BaseModel
from app.utils.database import execute_query, DatabaseError
import re


class Customer(BaseModel):
    """Customer model class"""
    
    _table_name = 'customer'
    _primary_key = 'customer_id'
    _fields = ['customer_id', 'first_name', 'family_name', 'email', 'phone']
    
    def __init__(self, **kwargs):
        """初始化客户实例"""
        super().__init__(**kwargs)
        
        # 属性验证
        if hasattr(self, 'email') and self.email:
            self._validate_email()
        if hasattr(self, 'phone') and self.phone:
            self._validate_phone()
    
    def _validate_email(self):
        """验证邮箱格式"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError(f"无效的邮箱格式: {self.email}")
    
    def _validate_phone(self):
        """验证手机号格式"""
        # 简单的手机号验证，可根据需要调整
        phone_pattern = r'^\d{10,11}$'
        if not re.match(phone_pattern, self.phone.replace(' ', '').replace('-', '')):
            raise ValueError(f"无效的手机号格式: {self.phone}")
    
    @property
    def full_name(self) -> str:
        """获取完整姓名"""
        first = self.first_name or ''
        family = self.family_name or ''
        return f"{first} {family}".strip()
    
    @classmethod
    def search_by_name(cls, search_term: str, search_type: str = 'both') -> List['Customer']:
        """
        根据姓名搜索客户
        
        Args:
            search_term: 搜索词
            search_type: 搜索类型 ('first_name', 'family_name', 'both')
        
        Returns:
            匹配的客户列表
        """
        try:
            search_term = f"%{search_term}%"
            
            if search_type == 'first_name':
                query = f"SELECT * FROM {cls._table_name} WHERE first_name LIKE %s ORDER BY family_name, first_name"
                params = (search_term,)
            elif search_type == 'family_name':
                query = f"SELECT * FROM {cls._table_name} WHERE family_name LIKE %s ORDER BY family_name, first_name"
                params = (search_term,)
            else:  # both
                query = f"""
                    SELECT * FROM {cls._table_name} 
                    WHERE first_name LIKE %s OR family_name LIKE %s 
                    ORDER BY family_name, first_name
                """
                params = (search_term, search_term)
            
            results = execute_query(query, params)
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            raise DatabaseError(f"搜索客户失败: {e}")
    
    @classmethod
    def get_all_sorted(cls) -> List['Customer']:
        """获取所有客户，按姓名排序"""
        return cls.find_all(order_by='family_name, first_name')
    
    def get_jobs(self, completed_only: bool = False) -> List[Dict[str, Any]]:
        """
        获取客户的工作订单
        
        Args:
            completed_only: 是否只获取已完成的订单
        
        Returns:
            工作订单列表
        """
        try:
            query = """
                SELECT j.*, 
                       CASE WHEN j.completed = 1 THEN 'YES' ELSE 'NO' END as completed_status,
                       CASE WHEN j.paid = 1 THEN 'YES' ELSE 'NO' END as paid_status
                FROM job j 
                WHERE j.customer = %s
            """
            
            if completed_only:
                query += " AND j.completed = 1"
            
            query += " ORDER BY j.job_date DESC"
            
            return execute_query(query, (self.customer_id,))
            
        except Exception as e:
            raise DatabaseError(f"获取客户工作订单失败: {e}")
    
    def get_unpaid_jobs(self) -> List[Dict[str, Any]]:
        """获取客户的未付款订单"""
        try:
            query = """
                SELECT j.*, 
                       DATEDIFF(CURDATE(), j.job_date) as days_since_job
                FROM job j 
                WHERE j.customer = %s AND j.paid = 0
                ORDER BY j.job_date ASC
            """
            
            return execute_query(query, (self.customer_id,))
            
        except Exception as e:
            raise DatabaseError(f"获取客户未付款订单失败: {e}")
    
    def get_total_unpaid_amount(self) -> float:
        """获取客户未付款总金额"""
        try:
            query = """
                SELECT COALESCE(SUM(total_cost), 0) as total_unpaid
                FROM job 
                WHERE customer = %s AND paid = 0
            """
            
            result = execute_query(query, (self.customer_id,), fetch_one=True)
            return float(result['total_unpaid']) if result else 0.0
            
        except Exception as e:
            raise DatabaseError(f"获取客户未付款总金额失败: {e}")
    
    def has_overdue_bills(self, days_threshold: int = 14) -> bool:
        """
        检查客户是否有逾期账单
        
        Args:
            days_threshold: 逾期天数阈值
        
        Returns:
            是否有逾期账单
        """
        try:
            query = """
                SELECT COUNT(*) as overdue_count
                FROM job 
                WHERE customer = %s 
                  AND paid = 0 
                  AND DATEDIFF(CURDATE(), job_date) > %s
            """
            
            result = execute_query(query, (self.customer_id, days_threshold), fetch_one=True)
            return result['overdue_count'] > 0 if result else False
            
        except Exception as e:
            raise DatabaseError(f"检查逾期账单失败: {e}")
    
    def validate(self) -> List[str]:
        """验证客户数据"""
        errors = []
        
        if not self.family_name or not self.family_name.strip():
            errors.append("姓氏不能为空")
        
        if not self.email or not self.email.strip():
            errors.append("邮箱不能为空")
        else:
            try:
                self._validate_email()
            except ValueError as e:
                errors.append(str(e))
        
        if not self.phone or not self.phone.strip():
            errors.append("手机号不能为空")
        else:
            try:
                self._validate_phone()
            except ValueError as e:
                errors.append(str(e))
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算字段"""
        data = super().to_dict()
        data['full_name'] = self.full_name
        return data 