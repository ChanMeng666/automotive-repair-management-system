"""
基础模型类
提供通用的数据库操作方法
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import logging
from app.utils.database import execute_query, execute_update, DatabaseError


class BaseModel(ABC):
    """基础模型类"""
    
    # 子类需要定义的属性
    _table_name: str = None
    _primary_key: str = 'id'
    _fields: List[str] = []
    
    def __init__(self, **kwargs):
        """初始化模型实例"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 设置属性
        for field in self._fields:
            setattr(self, field, kwargs.get(field))
    
    @classmethod
    def find_by_id(cls, pk_value: Any) -> Optional['BaseModel']:
        """根据主键查找记录"""
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE {cls._primary_key} = %s"
            result = execute_query(query, (pk_value,), fetch_one=True)
            
            if result:
                return cls(**result)
            return None
            
        except Exception as e:
            logging.error(f"查找记录失败 [{cls.__name__}]: {e}")
            raise DatabaseError(f"查找记录失败: {e}")
    
    @classmethod
    def find_all(cls, limit: Optional[int] = None, offset: int = 0, 
                 order_by: Optional[str] = None) -> List['BaseModel']:
        """查找所有记录"""
        try:
            query = f"SELECT * FROM {cls._table_name}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            results = execute_query(query)
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            logging.error(f"查找所有记录失败 [{cls.__name__}]: {e}")
            raise DatabaseError(f"查找所有记录失败: {e}")
    
    @classmethod
    def find_by_condition(cls, conditions: Dict[str, Any], 
                         limit: Optional[int] = None, 
                         order_by: Optional[str] = None) -> List['BaseModel']:
        """根据条件查找记录"""
        try:
            where_clause = " AND ".join([f"{key} = %s" for key in conditions.keys()])
            query = f"SELECT * FROM {cls._table_name} WHERE {where_clause}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT {limit}"
            
            params = tuple(conditions.values())
            results = execute_query(query, params)
            
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            logging.error(f"条件查找失败 [{cls.__name__}]: {e}")
            raise DatabaseError(f"条件查找失败: {e}")
    
    @classmethod
    def count(cls, conditions: Optional[Dict[str, Any]] = None) -> int:
        """统计记录数量"""
        try:
            query = f"SELECT COUNT(*) as count FROM {cls._table_name}"
            params = None
            
            if conditions:
                where_clause = " AND ".join([f"{key} = %s" for key in conditions.keys()])
                query += f" WHERE {where_clause}"
                params = tuple(conditions.values())
            
            result = execute_query(query, params, fetch_one=True)
            return result['count'] if result else 0
            
        except Exception as e:
            logging.error(f"统计记录失败 [{cls.__name__}]: {e}")
            raise DatabaseError(f"统计记录失败: {e}")
    
    def save(self) -> bool:
        """保存记录（新增或更新）"""
        try:
            pk_value = getattr(self, self._primary_key, None)
            
            if pk_value and self.find_by_id(pk_value):
                return self._update()
            else:
                return self._insert()
                
        except Exception as e:
            self.logger.error(f"保存记录失败: {e}")
            raise DatabaseError(f"保存记录失败: {e}")
    
    def _insert(self) -> bool:
        """插入新记录"""
        data = self._get_data_dict()
        
        # 排除主键（如果是自增的）
        if self._primary_key in data and data[self._primary_key] is None:
            data.pop(self._primary_key)
        
        fields = list(data.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)
        
        query = f"INSERT INTO {self._table_name} ({field_names}) VALUES ({placeholders})"
        params = tuple(data.values())
        
        affected_rows = execute_update(query, params)
        return affected_rows > 0
    
    def _update(self) -> bool:
        """更新记录"""
        data = self._get_data_dict()
        pk_value = data.pop(self._primary_key)
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {self._table_name} SET {set_clause} WHERE {self._primary_key} = %s"
        
        params = tuple(list(data.values()) + [pk_value])
        affected_rows = execute_update(query, params)
        return affected_rows > 0
    
    def delete(self) -> bool:
        """删除记录"""
        try:
            pk_value = getattr(self, self._primary_key)
            if not pk_value:
                raise ValueError("无法删除：缺少主键值")
            
            query = f"DELETE FROM {self._table_name} WHERE {self._primary_key} = %s"
            affected_rows = execute_update(query, (pk_value,))
            return affected_rows > 0
            
        except Exception as e:
            self.logger.error(f"删除记录失败: {e}")
            raise DatabaseError(f"删除记录失败: {e}")
    
    def _get_data_dict(self) -> Dict[str, Any]:
        """获取模型数据字典"""
        return {field: getattr(self, field, None) for field in self._fields}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._get_data_dict()
    
    def __repr__(self) -> str:
        """字符串表示"""
        pk_value = getattr(self, self._primary_key, 'Unknown')
        return f"<{self.__class__.__name__}({self._primary_key}={pk_value})>" 