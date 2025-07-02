"""
零件模型
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from .base import BaseModel
from app.utils.database import execute_query, DatabaseError


class Part(BaseModel):
    """零件模型类"""
    
    _table_name = 'part'
    _primary_key = 'part_id'
    _fields = ['part_id', 'part_name', 'cost']
    
    def __init__(self, **kwargs):
        """初始化零件实例"""
        super().__init__(**kwargs)
        
        # 类型转换
        if self.cost is not None:
            self.cost = Decimal(str(self.cost))
    
    @classmethod
    def get_all_sorted(cls) -> List['Part']:
        """获取所有零件，按名称排序"""
        return cls.find_all(order_by='part_name')
    
    @classmethod
    def search_by_name(cls, search_term: str) -> List['Part']:
        """根据零件名称搜索"""
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE part_name LIKE %s ORDER BY part_name"
            search_term = f"%{search_term}%"
            
            results = execute_query(query, (search_term,))
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            raise DatabaseError(f"搜索零件失败: {e}")
    
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
        """获取零件使用统计"""
        try:
            query = """
                SELECT 
                    COUNT(jp.job_id) as usage_count,
                    COALESCE(SUM(jp.qty), 0) as total_quantity,
                    COALESCE(SUM(jp.qty * p.cost), 0) as total_cost
                FROM part p
                LEFT JOIN job_part jp ON p.part_id = jp.part_id
                WHERE p.part_id = %s
            """
            
            result = execute_query(query, (self.part_id,), fetch_one=True)
            
            if result:
                return {
                    'usage_count': result['usage_count'],
                    'total_quantity': result['total_quantity'],
                    'total_cost': float(result['total_cost'])
                }
            
            return {
                'usage_count': 0,
                'total_quantity': 0,
                'total_cost': 0.0
            }
            
        except Exception as e:
            raise DatabaseError(f"获取零件使用统计失败: {e}")
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用该零件的工作订单"""
        try:
            query = """
                SELECT j.job_id, j.job_date, jp.qty,
                       c.first_name, c.family_name,
                       (jp.qty * p.cost) as part_cost
                FROM job_part jp
                JOIN job j ON jp.job_id = j.job_id
                JOIN customer c ON j.customer = c.customer_id
                JOIN part p ON jp.part_id = p.part_id
                WHERE jp.part_id = %s
                ORDER BY j.job_date DESC
                LIMIT %s
            """
            
            return execute_query(query, (self.part_id, limit))
            
        except Exception as e:
            raise DatabaseError(f"获取最近工作订单失败: {e}")
    
    @classmethod
    def get_inventory_report(cls) -> List[Dict[str, Any]]:
        """获取库存报告（包含使用统计）"""
        try:
            query = """
                SELECT p.part_id, p.part_name, p.cost,
                       COUNT(jp.job_id) as usage_count,
                       COALESCE(SUM(jp.qty), 0) as total_used,
                       COALESCE(SUM(jp.qty * p.cost), 0) as total_value
                FROM part p
                LEFT JOIN job_part jp ON p.part_id = jp.part_id
                GROUP BY p.part_id, p.part_name, p.cost
                ORDER BY usage_count DESC, p.part_name
            """
            
            results = execute_query(query)
            
            # 转换数据类型
            for result in results:
                result['cost'] = float(result['cost'])
                result['total_value'] = float(result['total_value'])
            
            return results
            
        except Exception as e:
            raise DatabaseError(f"获取库存报告失败: {e}")
    
    def validate(self) -> List[str]:
        """验证零件数据"""
        errors = []
        
        if not self.part_name or not self.part_name.strip():
            errors.append("零件名称不能为空")
        
        if self.cost is None:
            errors.append("零件成本不能为空")
        elif self.cost < 0:
            errors.append("零件成本不能为负数")
        
        # 检查零件名称是否重复
        if self.part_name:
            existing = self.find_by_condition({'part_name': self.part_name})
            if existing and (not self.part_id or existing[0].part_id != self.part_id):
                errors.append("零件名称已存在")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算字段"""
        data = super().to_dict()
        if self.cost:
            data['cost'] = float(self.cost)
        return data
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.part_name} (${self.cost})" 