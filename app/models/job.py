"""
工作订单模型
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from .base import BaseModel
from app.utils.database import execute_query, execute_update, DatabaseError


class Job(BaseModel):
    """工作订单模型类"""
    
    _table_name = 'job'
    _primary_key = 'job_id'
    _fields = ['job_id', 'job_date', 'customer', 'total_cost', 'completed', 'paid']
    
    def __init__(self, **kwargs):
        """初始化工作订单实例"""
        super().__init__(**kwargs)
        
        # 类型转换
        if isinstance(self.job_date, str):
            self.job_date = datetime.strptime(self.job_date, '%Y-%m-%d').date()
        
        if self.total_cost is not None:
            self.total_cost = Decimal(str(self.total_cost))
    
    @classmethod
    def get_current_jobs(cls, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取当前未完成的工作订单（分页）
        
        Args:
            page: 页码
            per_page: 每页记录数
        
        Returns:
            (工作订单列表, 总记录数)
        """
        try:
            offset = (page - 1) * per_page
            
            # 获取总记录数
            count_query = """
                SELECT COUNT(*) as total
                FROM job j
                JOIN customer c ON j.customer = c.customer_id
                WHERE j.completed = 0
            """
            count_result = execute_query(count_query, fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            # 获取分页数据
            query = """
                SELECT c.customer_id, c.first_name, c.family_name, 
                       j.job_id, j.job_date, j.total_cost, j.completed, j.paid
                FROM customer c 
                JOIN job j ON c.customer_id = j.customer
                WHERE j.completed = 0
                ORDER BY c.first_name, c.family_name, j.job_date DESC
                LIMIT %s OFFSET %s
            """
            
            results = execute_query(query, (per_page, offset))
            return results or [], total
            
        except Exception as e:
            raise DatabaseError(f"获取当前工作订单失败: {e}")
    
    @classmethod
    def get_all_with_customer_info(cls, order_by: str = "j.job_date DESC") -> List[Dict[str, Any]]:
        """获取所有工作订单及客户信息"""
        try:
            query = f"""
                SELECT c.customer_id, c.first_name, c.family_name,
                       j.job_id, j.job_date, j.total_cost, j.completed, j.paid
                FROM customer c
                JOIN job j ON c.customer_id = j.customer
                ORDER BY {order_by}
            """
            
            return execute_query(query)
            
        except Exception as e:
            raise DatabaseError(f"获取工作订单及客户信息失败: {e}")
    
    @classmethod
    def get_unpaid_jobs(cls, customer_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取未付款的工作订单
        
        Args:
            customer_name: 客户姓名过滤（可选）
        
        Returns:
            未付款工作订单列表
        """
        try:
            query = """
                SELECT j.job_id, j.job_date, j.total_cost, j.completed, j.paid,
                       c.customer_id, c.first_name, c.family_name
                FROM job j
                JOIN customer c ON j.customer = c.customer_id
                WHERE j.paid = 0
            """
            params = []
            
            if customer_name and customer_name != 'Choose...':
                query += " AND CONCAT(IFNULL(c.first_name, ''), ' ', c.family_name) = %s"
                params.append(customer_name)
            
            query += " ORDER BY c.family_name, c.first_name, j.job_date"
            
            return execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            raise DatabaseError(f"获取未付款工作订单失败: {e}")
    
    @classmethod
    def get_overdue_jobs(cls, days_threshold: int = 14) -> List[Dict[str, Any]]:
        """
        获取逾期的工作订单
        
        Args:
            days_threshold: 逾期天数阈值
        
        Returns:
            逾期工作订单列表
        """
        try:
            query = """
                SELECT j.job_id, j.job_date, j.total_cost, j.completed, j.paid,
                       c.customer_id, c.first_name, c.family_name,
                       DATEDIFF(CURDATE(), j.job_date) as days_overdue
                FROM job j
                JOIN customer c ON j.customer = c.customer_id
                WHERE j.paid = 0 
                  AND DATEDIFF(CURDATE(), j.job_date) > %s
                ORDER BY days_overdue DESC, j.job_date ASC
            """
            
            return execute_query(query, (days_threshold,))
            
        except Exception as e:
            raise DatabaseError(f"获取逾期工作订单失败: {e}")
    
    def get_job_details(self) -> Dict[str, Any]:
        """获取工作订单详细信息（包含客户信息）"""
        try:
            query = """
                SELECT c.customer_id, c.first_name, c.family_name,
                       j.job_id, j.job_date, j.total_cost, j.completed, j.paid
                FROM customer c
                JOIN job j ON c.customer_id = j.customer
                WHERE j.job_id = %s
            """
            
            return execute_query(query, (self.job_id,), fetch_one=True)
            
        except Exception as e:
            raise DatabaseError(f"获取工作订单详情失败: {e}")
    
    def get_services(self) -> List[Dict[str, Any]]:
        """获取工作订单的服务项目"""
        try:
            query = """
                SELECT s.service_name, js.qty, s.cost,
                       (js.qty * s.cost) as total_cost
                FROM service s
                JOIN job_service js ON s.service_id = js.service_id
                WHERE js.job_id = %s
                ORDER BY s.service_name
            """
            
            return execute_query(query, (self.job_id,))
            
        except Exception as e:
            raise DatabaseError(f"获取工作订单服务项目失败: {e}")
    
    def get_parts(self) -> List[Dict[str, Any]]:
        """获取工作订单的零件"""
        try:
            query = """
                SELECT p.part_name, jp.qty, p.cost,
                       (jp.qty * p.cost) as total_cost
                FROM part p
                JOIN job_part jp ON p.part_id = jp.part_id
                WHERE jp.job_id = %s
                ORDER BY p.part_name
            """
            
            return execute_query(query, (self.job_id,))
            
        except Exception as e:
            raise DatabaseError(f"获取工作订单零件失败: {e}")
    
    def add_service(self, service_id: int, quantity: int) -> bool:
        """
        为工作订单添加服务
        
        Args:
            service_id: 服务ID
            quantity: 数量
        
        Returns:
            是否添加成功
        """
        try:
            # 检查工作订单是否已完成
            if self.completed:
                raise ValueError("无法修改已完成的工作订单")
            
            # 添加服务到job_service表
            query = """
                INSERT INTO job_service (job_id, service_id, qty) 
                VALUES (%s, %s, %s)
            """
            execute_update(query, (self.job_id, service_id, quantity))
            
            # 更新总成本
            self._update_total_cost()
            return True
            
        except Exception as e:
            raise DatabaseError(f"添加服务失败: {e}")
    
    def add_part(self, part_id: int, quantity: int) -> bool:
        """
        为工作订单添加零件
        
        Args:
            part_id: 零件ID
            quantity: 数量
        
        Returns:
            是否添加成功
        """
        try:
            # 检查工作订单是否已完成
            if self.completed:
                raise ValueError("无法修改已完成的工作订单")
            
            # 添加零件到job_part表
            query = """
                INSERT INTO job_part (job_id, part_id, qty) 
                VALUES (%s, %s, %s)
            """
            execute_update(query, (self.job_id, part_id, quantity))
            
            # 更新总成本
            self._update_total_cost()
            return True
            
        except Exception as e:
            raise DatabaseError(f"添加零件失败: {e}")
    
    def mark_as_completed(self) -> bool:
        """标记工作订单为已完成"""
        try:
            query = "UPDATE job SET completed = 1 WHERE job_id = %s"
            affected_rows = execute_update(query, (self.job_id,))
            
            if affected_rows > 0:
                self.completed = 1
                return True
            return False
            
        except Exception as e:
            raise DatabaseError(f"标记工作订单完成失败: {e}")
    
    def mark_as_paid(self) -> bool:
        """标记工作订单为已付款"""
        try:
            query = "UPDATE job SET paid = 1 WHERE job_id = %s"
            affected_rows = execute_update(query, (self.job_id,))
            
            if affected_rows > 0:
                self.paid = 1
                return True
            return False
            
        except Exception as e:
            raise DatabaseError(f"标记工作订单付款失败: {e}")
    
    def _update_total_cost(self) -> None:
        """更新工作订单总成本"""
        try:
            # 计算服务总成本
            service_query = """
                SELECT COALESCE(SUM(js.qty * s.cost), 0) as service_total
                FROM job_service js
                JOIN service s ON js.service_id = s.service_id
                WHERE js.job_id = %s
            """
            service_result = execute_query(service_query, (self.job_id,), fetch_one=True)
            service_total = service_result['service_total'] if service_result else 0
            
            # 计算零件总成本
            part_query = """
                SELECT COALESCE(SUM(jp.qty * p.cost), 0) as part_total
                FROM job_part jp
                JOIN part p ON jp.part_id = p.part_id
                WHERE jp.job_id = %s
            """
            part_result = execute_query(part_query, (self.job_id,), fetch_one=True)
            part_total = part_result['part_total'] if part_result else 0
            
            # 更新总成本
            new_total = Decimal(str(service_total)) + Decimal(str(part_total))
            update_query = "UPDATE job SET total_cost = %s WHERE job_id = %s"
            execute_update(update_query, (float(new_total), self.job_id))
            
            self.total_cost = new_total
            
        except Exception as e:
            raise DatabaseError(f"更新总成本失败: {e}")
    
    @property
    def is_overdue(self, days_threshold: int = 14) -> bool:
        """检查是否逾期"""
        if self.paid or not self.job_date:
            return False
        
        days_diff = (date.today() - self.job_date).days
        return days_diff > days_threshold
    
    @property
    def status_text(self) -> str:
        """获取状态文本"""
        if self.completed and self.paid:
            return "已完成并付款"
        elif self.completed:
            return "已完成未付款"
        else:
            return "进行中"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算字段"""
        data = super().to_dict()
        data['is_overdue'] = self.is_overdue
        data['status_text'] = self.status_text
        if self.total_cost:
            data['total_cost'] = float(self.total_cost)
        return data 