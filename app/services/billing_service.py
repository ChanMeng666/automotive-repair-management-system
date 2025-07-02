"""
账单服务类
封装账单和付款相关的业务逻辑
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, timedelta
import logging
from app.models.job import Job
from app.models.customer import Customer
from app.utils.database import execute_query, execute_update, DatabaseError


class BillingService:
    """账单服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_unpaid_bills(self, customer_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取未付款账单
        
        Args:
            customer_name: 客户姓名过滤（可选）
        
        Returns:
            未付款账单列表
        """
        try:
            return Job.get_unpaid_jobs(customer_name)
        except Exception as e:
            self.logger.error(f"获取未付款账单失败: {e}")
            return []
    
    def get_overdue_bills(self, days_threshold: int = 14) -> List[Dict[str, Any]]:
        """
        获取逾期账单
        
        Args:
            days_threshold: 逾期天数阈值
        
        Returns:
            逾期账单列表
        """
        try:
            bills = Job.get_overdue_jobs(days_threshold)
            
            # 添加逾期状态
            for bill in bills:
                bill['overdue'] = True
                bill['days_overdue'] = bill.get('days_overdue', 0)
            
            return bills
            
        except Exception as e:
            self.logger.error(f"获取逾期账单失败: {e}")
            return []
    
    def get_all_bills_with_status(self) -> List[Dict[str, Any]]:
        """获取所有账单及其状态"""
        try:
            # 获取所有工作订单
            bills = Job.get_all_with_customer_info()
            
            # 添加逾期状态
            today = date.today()
            for bill in bills:
                job_date = bill.get('job_date')
                if isinstance(job_date, str):
                    job_date = date.fromisoformat(job_date)
                
                # 计算逾期天数
                if job_date and not bill.get('paid'):
                    days_diff = (today - job_date).days
                    bill['overdue'] = days_diff > 14
                    bill['days_overdue'] = days_diff if days_diff > 14 else 0
                else:
                    bill['overdue'] = False
                    bill['days_overdue'] = 0
            
            return bills
            
        except Exception as e:
            self.logger.error(f"获取所有账单失败: {e}")
            return []
    
    def mark_customer_bills_as_paid(self, customer_id: int) -> Tuple[bool, List[str], int]:
        """
        标记客户的所有未付款账单为已付款
        
        Args:
            customer_id: 客户ID
        
        Returns:
            (是否成功, 错误信息列表, 标记付款的账单数量)
        """
        try:
            # 验证客户存在
            customer = Customer.find_by_id(customer_id)
            if not customer:
                return False, ["客户不存在"], 0
            
            # 获取客户的未付款账单
            unpaid_jobs = customer.get_unpaid_jobs()
            if not unpaid_jobs:
                return False, ["该客户没有未付款账单"], 0
            
            # 批量更新为已付款
            job_ids = [job['job_id'] for job in unpaid_jobs]
            placeholders = ','.join(['%s'] * len(job_ids))
            query = f"UPDATE job SET paid = 1 WHERE job_id IN ({placeholders})"
            
            affected_rows = execute_update(query, tuple(job_ids))
            
            if affected_rows > 0:
                self.logger.info(f"客户 {customer.full_name} 的 {affected_rows} 个账单标记为已付款")
                return True, [], affected_rows
            else:
                return False, ["标记付款失败"], 0
                
        except Exception as e:
            self.logger.error(f"标记客户账单付款失败: {e}")
            return False, ["系统错误，请稍后重试"], 0
    
    def mark_job_as_paid(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        标记单个工作订单为已付款
        
        Args:
            job_id: 工作订单ID
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            job = Job.find_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.paid:
                return False, ["账单已经付款"]
            
            success = job.mark_as_paid()
            if success:
                self.logger.info(f"工作订单 {job_id} 标记为已付款")
                return True, []
            else:
                return False, ["标记付款失败"]
                
        except Exception as e:
            self.logger.error(f"标记账单付款失败: {e}")
            return False, ["系统错误，请稍后重试"]
    
    def get_customer_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """
        获取客户账单汇总
        
        Args:
            customer_id: 客户ID
        
        Returns:
            客户账单汇总信息
        """
        try:
            customer = Customer.find_by_id(customer_id)
            if not customer:
                return {}
            
            # 获取所有账单
            all_jobs = customer.get_jobs()
            unpaid_jobs = customer.get_unpaid_jobs()
            
            # 计算汇总信息
            total_amount = sum(float(job.get('total_cost', 0)) for job in all_jobs)
            unpaid_amount = sum(float(job.get('total_cost', 0)) for job in unpaid_jobs)
            paid_amount = total_amount - unpaid_amount
            
            # 逾期账单
            overdue_jobs = [job for job in unpaid_jobs 
                           if self._is_job_overdue(job)]
            overdue_amount = sum(float(job.get('total_cost', 0)) for job in overdue_jobs)
            
            return {
                'customer_info': customer.to_dict(),
                'total_jobs': len(all_jobs),
                'total_amount': total_amount,
                'paid_jobs': len(all_jobs) - len(unpaid_jobs),
                'paid_amount': paid_amount,
                'unpaid_jobs': len(unpaid_jobs),
                'unpaid_amount': unpaid_amount,
                'overdue_jobs': len(overdue_jobs),
                'overdue_amount': overdue_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取客户账单汇总失败: {e}")
            return {}
    
    def get_billing_statistics(self) -> Dict[str, Any]:
        """获取账单统计信息"""
        try:
            # 总账单统计
            query = """
                SELECT 
                    COUNT(*) as total_bills,
                    COALESCE(SUM(total_cost), 0) as total_amount,
                    COUNT(CASE WHEN paid = 1 THEN 1 END) as paid_bills,
                    COALESCE(SUM(CASE WHEN paid = 1 THEN total_cost ELSE 0 END), 0) as paid_amount,
                    COUNT(CASE WHEN paid = 0 THEN 1 END) as unpaid_bills,
                    COALESCE(SUM(CASE WHEN paid = 0 THEN total_cost ELSE 0 END), 0) as unpaid_amount
                FROM job
                WHERE total_cost > 0
            """
            
            result = execute_query(query, fetch_one=True)
            
            if not result:
                return self._get_empty_billing_stats()
            
            # 逾期账单统计
            overdue_bills = self.get_overdue_bills()
            overdue_amount = sum(float(bill.get('total_cost', 0)) for bill in overdue_bills)
            
            # 本月统计
            today = date.today()
            month_start = today.replace(day=1)
            
            month_query = """
                SELECT 
                    COUNT(*) as month_bills,
                    COALESCE(SUM(total_cost), 0) as month_amount,
                    COUNT(CASE WHEN paid = 1 THEN 1 END) as month_paid_bills,
                    COALESCE(SUM(CASE WHEN paid = 1 THEN total_cost ELSE 0 END), 0) as month_paid_amount
                FROM job
                WHERE job_date >= %s AND total_cost > 0
            """
            
            month_result = execute_query(month_query, (month_start,), fetch_one=True)
            
            total_amount = float(result['total_amount'])
            paid_amount = float(result['paid_amount'])
            unpaid_amount = float(result['unpaid_amount'])
            
            return {
                'total_bills': result['total_bills'],
                'total_amount': total_amount,
                'paid_bills': result['paid_bills'],
                'paid_amount': paid_amount,
                'unpaid_bills': result['unpaid_bills'],
                'unpaid_amount': unpaid_amount,
                'overdue_bills': len(overdue_bills),
                'overdue_amount': overdue_amount,
                'payment_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0,
                'month_bills': month_result['month_bills'] if month_result else 0,
                'month_amount': float(month_result['month_amount']) if month_result else 0,
                'month_paid_bills': month_result['month_paid_bills'] if month_result else 0,
                'month_paid_amount': float(month_result['month_paid_amount']) if month_result else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取账单统计失败: {e}")
            return self._get_empty_billing_stats()
    
    def get_customers_with_unpaid_bills(self) -> List[Dict[str, Any]]:
        """获取有未付款账单的客户列表"""
        try:
            query = """
                SELECT DISTINCT c.customer_id, c.first_name, c.family_name, c.email, c.phone,
                       COUNT(j.job_id) as unpaid_count,
                       COALESCE(SUM(j.total_cost), 0) as unpaid_amount
                FROM customer c
                JOIN job j ON c.customer_id = j.customer
                WHERE j.paid = 0
                GROUP BY c.customer_id, c.first_name, c.family_name, c.email, c.phone
                ORDER BY unpaid_amount DESC, c.family_name, c.first_name
            """
            
            results = execute_query(query)
            
            # 转换数据类型
            for result in results:
                result['unpaid_amount'] = float(result['unpaid_amount'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取有未付款账单的客户失败: {e}")
            return []
    
    def _is_job_overdue(self, job: Dict[str, Any], days_threshold: int = 14) -> bool:
        """检查工作订单是否逾期"""
        if job.get('paid'):
            return False
        
        job_date = job.get('job_date')
        if isinstance(job_date, str):
            job_date = date.fromisoformat(job_date)
        
        if job_date:
            days_diff = (date.today() - job_date).days
            return days_diff > days_threshold
        
        return False
    
    def _get_empty_billing_stats(self) -> Dict[str, Any]:
        """返回空的账单统计"""
        return {
            'total_bills': 0,
            'total_amount': 0.0,
            'paid_bills': 0,
            'paid_amount': 0.0,
            'unpaid_bills': 0,
            'unpaid_amount': 0.0,
            'overdue_bills': 0,
            'overdue_amount': 0.0,
            'payment_rate': 0.0,
            'month_bills': 0,
            'month_amount': 0.0,
            'month_paid_bills': 0,
            'month_paid_amount': 0.0
        } 