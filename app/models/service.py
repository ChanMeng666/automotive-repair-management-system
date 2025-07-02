"""
服务模型
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from .base import BaseModel
from app.utils.database import execute_query, DatabaseError


class Service(BaseModel):
    """服务模型类"""
    
    _table_name = 'service'
    _primary_key = 'service_id'
    _fields = ['service_id', 'service_name', 'cost']
    
    def __init__(self, **kwargs):
        """初始化服务实例"""
        super().__init__(**kwargs)
        
        # 类型转换
        if self.cost is not None:
            self.cost = Decimal(str(self.cost))
    
    @classmethod
    def get_all_sorted(cls) -> List['Service']:
        """获取所有服务，按名称排序"""
        return cls.find_all(order_by='service_name')
    
    @classmethod
    def search_by_name(cls, search_term: str) -> List['Service']:
        """根据服务名称搜索"""
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE service_name LIKE %s ORDER BY service_name"
            search_term = f"%{search_term}%"
            
            results = execute_query(query, (search_term,))
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            raise DatabaseError(f"搜索服务失败: {e}")
    
    def calculate_total_cost(self, quantity: int) -> Decimal:
        """
        计算指定数量的总成本
        
        Args:
            quantity: 数量
        
        Returns:
            总成本
        """
        if not self.cost or quantity <= 0:
            return Decimal('0')
        
        return self.cost * Decimal(str(quantity))
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """获取服务使用统计"""
        try:
            query = """
                SELECT 
                    COUNT(js.job_id) as usage_count,
                    COALESCE(SUM(js.qty), 0) as total_quantity,
                    COALESCE(SUM(js.qty * s.cost), 0) as total_revenue
                FROM service s
                LEFT JOIN job_service js ON s.service_id = js.service_id
                WHERE s.service_id = %s
            """
            
            result = execute_query(query, (self.service_id,), fetch_one=True)
            
            if result:
                return {
                    'usage_count': result['usage_count'],
                    'total_quantity': result['total_quantity'],
                    'total_revenue': float(result['total_revenue'])
                }
            
            return {
                'usage_count': 0,
                'total_quantity': 0,
                'total_revenue': 0.0
            }
            
        except Exception as e:
            raise DatabaseError(f"获取服务使用统计失败: {e}")
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用该服务的工作订单"""
        try:
            query = """
                SELECT j.job_id, j.job_date, js.qty,
                       c.first_name, c.family_name,
                       (js.qty * s.cost) as service_cost
                FROM job_service js
                JOIN job j ON js.job_id = j.job_id
                JOIN customer c ON j.customer = c.customer_id
                JOIN service s ON js.service_id = s.service_id
                WHERE js.service_id = %s
                ORDER BY j.job_date DESC
                LIMIT %s
            """
            
            return execute_query(query, (self.service_id, limit))
            
        except Exception as e:
            raise DatabaseError(f"获取最近工作订单失败: {e}")
    
    def validate(self) -> List[str]:
        """验证服务数据"""
        errors = []
        
        if not self.service_name or not self.service_name.strip():
            errors.append("服务名称不能为空")
        
        if self.cost is None:
            errors.append("服务成本不能为空")
        elif self.cost < 0:
            errors.append("服务成本不能为负数")
        
        # 检查服务名称是否重复
        if self.service_name:
            existing = self.find_by_condition({'service_name': self.service_name})
            if existing and (not self.service_id or existing[0].service_id != self.service_id):
                errors.append("服务名称已存在")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算字段"""
        data = super().to_dict()
        if self.cost:
            data['cost'] = float(self.cost)
        return data
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.service_name} (${self.cost})" 