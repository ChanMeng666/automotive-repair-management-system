"""
客户服务类
封装客户相关的业务逻辑
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import logging
from app.models.customer import Customer
from app.models.job import Job
from app.utils.database import DatabaseError, ValidationError


class CustomerService:
    """客户服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_all_customers(self, sorted_by_name: bool = True) -> List[Customer]:
        """
        获取所有客户
        
        Args:
            sorted_by_name: 是否按姓名排序
        
        Returns:
            客户列表
        """
        try:
            if sorted_by_name:
                return Customer.get_all_sorted()
            else:
                return Customer.find_all()
                
        except Exception as e:
            self.logger.error(f"获取客户列表失败: {e}")
            raise DatabaseError("获取客户列表失败")
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """根据ID获取客户"""
        try:
            return Customer.find_by_id(customer_id)
        except Exception as e:
            self.logger.error(f"获取客户失败 (ID: {customer_id}): {e}")
            raise DatabaseError("获取客户信息失败")
    
    def search_customers(self, search_term: str, search_type: str = 'both') -> List[Customer]:
        """
        搜索客户
        
        Args:
            search_term: 搜索关键词
            search_type: 搜索类型 ('first_name', 'family_name', 'both')
        
        Returns:
            匹配的客户列表
        """
        try:
            if not search_term or not search_term.strip():
                return self.get_all_customers()
            
            return Customer.search_by_name(search_term.strip(), search_type)
            
        except Exception as e:
            self.logger.error(f"搜索客户失败: {e}")
            raise DatabaseError("搜索客户失败")
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Customer]]:
        """
        创建新客户
        
        Args:
            customer_data: 客户数据字典
        
        Returns:
            (是否成功, 错误信息列表, 客户对象)
        """
        try:
            # 创建客户对象
            customer = Customer(**customer_data)
            
            # 验证数据
            validation_errors = customer.validate()
            if validation_errors:
                return False, validation_errors, None
            
            # 保存客户
            success = customer.save()
            if success:
                self.logger.info(f"客户创建成功: {customer.full_name}")
                return True, [], customer
            else:
                return False, ["保存客户失败"], None
                
        except ValueError as e:
            return False, [str(e)], None
        except Exception as e:
            self.logger.error(f"创建客户失败: {e}")
            return False, ["系统错误，请稍后重试"], None
    
    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Customer]]:
        """
        更新客户信息
        
        Args:
            customer_id: 客户ID
            customer_data: 更新的客户数据
        
        Returns:
            (是否成功, 错误信息列表, 客户对象)
        """
        try:
            # 获取现有客户
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["客户不存在"], None
            
            # 更新属性
            for key, value in customer_data.items():
                if hasattr(customer, key) and key in Customer._fields:
                    setattr(customer, key, value)
            
            # 验证数据
            validation_errors = customer.validate()
            if validation_errors:
                return False, validation_errors, None
            
            # 保存更新
            success = customer.save()
            if success:
                self.logger.info(f"客户更新成功: {customer.full_name}")
                return True, [], customer
            else:
                return False, ["更新客户失败"], None
                
        except Exception as e:
            self.logger.error(f"更新客户失败 (ID: {customer_id}): {e}")
            return False, ["系统错误，请稍后重试"], None
    
    def delete_customer(self, customer_id: int) -> Tuple[bool, List[str]]:
        """
        删除客户
        
        Args:
            customer_id: 客户ID
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["客户不存在"]
            
            # 检查是否有关联的工作订单
            jobs = customer.get_jobs()
            if jobs:
                return False, ["无法删除有工作订单的客户"]
            
            # 删除客户
            success = customer.delete()
            if success:
                self.logger.info(f"客户删除成功: {customer.full_name}")
                return True, []
            else:
                return False, ["删除客户失败"]
                
        except Exception as e:
            self.logger.error(f"删除客户失败 (ID: {customer_id}): {e}")
            return False, ["系统错误，请稍后重试"]
    
    def get_customer_jobs(self, customer_id: int, completed_only: bool = False) -> List[Dict[str, Any]]:
        """获取客户的工作订单"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return []
            
            return customer.get_jobs(completed_only)
            
        except Exception as e:
            self.logger.error(f"获取客户工作订单失败 (ID: {customer_id}): {e}")
            return []
    
    def get_customer_unpaid_jobs(self, customer_id: int) -> List[Dict[str, Any]]:
        """获取客户的未付款订单"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return []
            
            return customer.get_unpaid_jobs()
            
        except Exception as e:
            self.logger.error(f"获取客户未付款订单失败 (ID: {customer_id}): {e}")
            return []
    
    def get_customer_statistics(self, customer_id: int) -> Dict[str, Any]:
        """
        获取客户统计信息
        
        Args:
            customer_id: 客户ID
        
        Returns:
            客户统计信息字典
        """
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return {}
            
            all_jobs = customer.get_jobs()
            unpaid_jobs = customer.get_unpaid_jobs()
            total_unpaid = customer.get_total_unpaid_amount()
            has_overdue = customer.has_overdue_bills()
            
            return {
                'customer_info': customer.to_dict(),
                'total_jobs': len(all_jobs),
                'completed_jobs': len([j for j in all_jobs if j.get('completed') == 1]),
                'unpaid_jobs': len(unpaid_jobs),
                'total_unpaid_amount': total_unpaid,
                'has_overdue_bills': has_overdue,
                'recent_jobs': all_jobs[:5]  # 最近5个订单
            }
            
        except Exception as e:
            self.logger.error(f"获取客户统计信息失败 (ID: {customer_id}): {e}")
            return {}
    
    def get_customers_with_filter(self, 
                                 has_unpaid: Optional[bool] = None,
                                 has_overdue: Optional[bool] = None,
                                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        根据条件过滤客户
        
        Args:
            has_unpaid: 是否有未付款订单
            has_overdue: 是否有逾期订单
            limit: 限制返回数量
        
        Returns:
            过滤后的客户列表
        """
        try:
            customers = self.get_all_customers()
            filtered_customers = []
            
            for customer in customers:
                include = True
                
                if has_unpaid is not None:
                    unpaid_amount = customer.get_total_unpaid_amount()
                    if has_unpaid and unpaid_amount <= 0:
                        include = False
                    elif not has_unpaid and unpaid_amount > 0:
                        include = False
                
                if include and has_overdue is not None:
                    is_overdue = customer.has_overdue_bills()
                    if has_overdue and not is_overdue:
                        include = False
                    elif not has_overdue and is_overdue:
                        include = False
                
                if include:
                    customer_data = customer.to_dict()
                    customer_data['total_unpaid'] = customer.get_total_unpaid_amount()
                    customer_data['has_overdue'] = customer.has_overdue_bills()
                    filtered_customers.append(customer_data)
                
                if limit and len(filtered_customers) >= limit:
                    break
            
            return filtered_customers
            
        except Exception as e:
            self.logger.error(f"过滤客户失败: {e}")
            return []
    
    def schedule_job_for_customer(self, customer_id: int, job_date: date) -> Tuple[bool, List[str], Optional[int]]:
        """
        为客户安排工作订单
        
        Args:
            customer_id: 客户ID
            job_date: 工作日期
        
        Returns:
            (是否成功, 错误信息列表, 工作订单ID)
        """
        try:
            # 验证客户存在
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, ["客户不存在"], None
            
            # 验证日期
            if job_date < date.today():
                return False, ["工作日期不能早于今天"], None
            
            # 创建工作订单
            job_data = {
                'job_date': job_date,
                'customer': customer_id,
                'total_cost': 0.0,
                'completed': 0,
                'paid': 0
            }
            
            job = Job(**job_data)
            success = job.save()
            
            if success:
                self.logger.info(f"为客户 {customer.full_name} 安排工作订单成功")
                return True, [], job.job_id
            else:
                return False, ["创建工作订单失败"], None
                
        except Exception as e:
            self.logger.error(f"安排工作订单失败: {e}")
            return False, ["系统错误，请稍后重试"], None 