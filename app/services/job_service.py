"""
工作订单服务类
封装工作订单相关的业务逻辑
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import logging
from app.models.job import Job
from app.models.service import Service
from app.models.part import Part
from app.utils.database import DatabaseError, ValidationError


class JobService:
    """工作订单服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_current_jobs(self, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        获取当前未完成的工作订单（分页）
        
        Args:
            page: 页码
            per_page: 每页记录数
        
        Returns:
            (工作订单列表, 总记录数, 总页数)
        """
        try:
            jobs, total = Job.get_current_jobs(page, per_page)
            total_pages = (total + per_page - 1) // per_page
            
            return jobs, total, total_pages
            
        except Exception as e:
            self.logger.error(f"获取当前工作订单失败: {e}")
            raise DatabaseError("获取工作订单列表失败")
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """根据ID获取工作订单"""
        try:
            return Job.find_by_id(job_id)
        except Exception as e:
            self.logger.error(f"获取工作订单失败 (ID: {job_id}): {e}")
            raise DatabaseError("获取工作订单信息失败")
    
    def get_job_details(self, job_id: int) -> Dict[str, Any]:
        """
        获取工作订单详细信息
        
        Args:
            job_id: 工作订单ID
        
        Returns:
            工作订单详细信息字典
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return {}
            
            # 获取基本信息
            job_details = job.get_job_details()
            if not job_details:
                return {}
            
            # 获取服务和零件
            services = job.get_services()
            parts = job.get_parts()
            
            # 获取所有可用的服务和零件
            all_services = Service.get_all_sorted()
            all_parts = Part.get_all_sorted()
            
            return {
                'job_info': job_details,
                'services': services,
                'parts': parts,
                'all_services': [s.to_dict() for s in all_services],
                'all_parts': [p.to_dict() for p in all_parts],
                'job_completed': bool(job_details.get('completed'))
            }
            
        except Exception as e:
            self.logger.error(f"获取工作订单详情失败 (ID: {job_id}): {e}")
            return {}
    
    def add_service_to_job(self, job_id: int, service_id: int, quantity: int) -> Tuple[bool, List[str]]:
        """
        为工作订单添加服务
        
        Args:
            job_id: 工作订单ID
            service_id: 服务ID
            quantity: 数量
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            # 验证参数
            if quantity <= 0:
                return False, ["数量必须大于0"]
            
            # 获取工作订单
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.completed:
                return False, ["无法修改已完成的工作订单"]
            
            # 验证服务存在
            service = Service.find_by_id(service_id)
            if not service:
                return False, ["服务不存在"]
            
            # 添加服务
            success = job.add_service(service_id, quantity)
            if success:
                self.logger.info(f"为工作订单 {job_id} 添加服务 {service.service_name} 成功")
                return True, []
            else:
                return False, ["添加服务失败"]
                
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.logger.error(f"添加服务失败: {e}")
            return False, ["系统错误，请稍后重试"]
    
    def add_part_to_job(self, job_id: int, part_id: int, quantity: int) -> Tuple[bool, List[str]]:
        """
        为工作订单添加零件
        
        Args:
            job_id: 工作订单ID
            part_id: 零件ID
            quantity: 数量
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            # 验证参数
            if quantity <= 0:
                return False, ["数量必须大于0"]
            
            # 获取工作订单
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.completed:
                return False, ["无法修改已完成的工作订单"]
            
            # 验证零件存在
            part = Part.find_by_id(part_id)
            if not part:
                return False, ["零件不存在"]
            
            # 添加零件
            success = job.add_part(part_id, quantity)
            if success:
                self.logger.info(f"为工作订单 {job_id} 添加零件 {part.part_name} 成功")
                return True, []
            else:
                return False, ["添加零件失败"]
                
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.logger.error(f"添加零件失败: {e}")
            return False, ["系统错误，请稍后重试"]
    
    def mark_job_as_completed(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        标记工作订单为已完成
        
        Args:
            job_id: 工作订单ID
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.completed:
                return False, ["工作订单已经完成"]
            
            success = job.mark_as_completed()
            if success:
                self.logger.info(f"工作订单 {job_id} 标记为完成")
                return True, []
            else:
                return False, ["标记完成失败"]
                
        except Exception as e:
            self.logger.error(f"标记工作订单完成失败: {e}")
            return False, ["系统错误，请稍后重试"]
    
    def mark_job_as_paid(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        标记工作订单为已付款
        
        Args:
            job_id: 工作订单ID
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.paid:
                return False, ["工作订单已经付款"]
            
            success = job.mark_as_paid()
            if success:
                self.logger.info(f"工作订单 {job_id} 标记为已付款")
                return True, []
            else:
                return False, ["标记付款失败"]
                
        except Exception as e:
            self.logger.error(f"标记工作订单付款失败: {e}")
            return False, ["系统错误，请稍后重试"]
    
    def get_all_jobs_with_customer_info(self) -> List[Dict[str, Any]]:
        """获取所有工作订单及客户信息"""
        try:
            return Job.get_all_with_customer_info()
        except Exception as e:
            self.logger.error(f"获取所有工作订单失败: {e}")
            return []
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """获取工作订单统计信息"""
        try:
            # 总订单数
            total_jobs = Job.count()
            
            # 已完成订单数
            completed_jobs = Job.count({'completed': 1})
            
            # 未付款订单数
            unpaid_jobs = Job.count({'paid': 0})
            
            # 逾期订单数
            overdue_jobs = Job.get_overdue_jobs()
            
            # 今日新订单数
            today = date.today()
            today_jobs = Job.count({'job_date': today})
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'pending_jobs': total_jobs - completed_jobs,
                'unpaid_jobs': unpaid_jobs,
                'overdue_jobs': len(overdue_jobs),
                'today_new_jobs': today_jobs,
                'completion_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'payment_rate': ((total_jobs - unpaid_jobs) / total_jobs * 100) if total_jobs > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取工作订单统计失败: {e}")
            return {
                'total_jobs': 0,
                'completed_jobs': 0,
                'pending_jobs': 0,
                'unpaid_jobs': 0,
                'overdue_jobs': 0,
                'today_new_jobs': 0,
                'completion_rate': 0,
                'payment_rate': 0
            }
    
    def create_job(self, customer_id: int, job_date: date) -> Tuple[bool, List[str], Optional[Job]]:
        """
        创建新的工作订单
        
        Args:
            customer_id: 客户ID
            job_date: 工作日期
        
        Returns:
            (是否成功, 错误信息列表, 工作订单对象)
        """
        try:
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
                self.logger.info(f"创建工作订单成功 (客户ID: {customer_id})")
                return True, [], job
            else:
                return False, ["创建工作订单失败"], None
                
        except Exception as e:
            self.logger.error(f"创建工作订单失败: {e}")
            return False, ["系统错误，请稍后重试"], None
    
    def delete_job(self, job_id: int) -> Tuple[bool, List[str]]:
        """
        删除工作订单
        
        Args:
            job_id: 工作订单ID
        
        Returns:
            (是否成功, 错误信息列表)
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return False, ["工作订单不存在"]
            
            if job.completed:
                return False, ["无法删除已完成的工作订单"]
            
            # 检查是否有关联的服务和零件
            services = job.get_services()
            parts = job.get_parts()
            
            if services or parts:
                return False, ["无法删除有服务或零件的工作订单"]
            
            success = job.delete()
            if success:
                self.logger.info(f"删除工作订单成功 (ID: {job_id})")
                return True, []
            else:
                return False, ["删除工作订单失败"]
                
        except Exception as e:
            self.logger.error(f"删除工作订单失败: {e}")
            return False, ["系统错误，请稍后重试"] 