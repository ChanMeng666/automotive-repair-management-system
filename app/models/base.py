"""
Base model class
Provides common database operation methods
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import logging
from app.utils.database import execute_query, execute_update, DatabaseError


class BaseModel(ABC):
    """Base model class"""
    
    # Attributes that subclasses need to define
    _table_name: str = None
    _primary_key: str = 'id'
    _fields: List[str] = []
    
    def __init__(self, **kwargs):
        """Initialize model instance"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set attributes
        for field in self._fields:
            setattr(self, field, kwargs.get(field))
    
    @classmethod
    def find_by_id(cls, pk_value: Any) -> Optional['BaseModel']:
        """Find record by primary key"""
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE {cls._primary_key} = %s"
            result = execute_query(query, (pk_value,), fetch_one=True)
            
            if result:
                return cls(**result)
            return None
            
        except Exception as e:
            logging.error(f"Failed to find record [{cls.__name__}]: {e}")
            raise DatabaseError(f"Failed to find record: {e}")
    
    @classmethod
    def find_all(cls, limit: Optional[int] = None, offset: int = 0, 
                 order_by: Optional[str] = None) -> List['BaseModel']:
        """Find all records"""
        try:
            query = f"SELECT * FROM {cls._table_name}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            results = execute_query(query)
            return [cls(**row) for row in results] if results else []
            
        except Exception as e:
            logging.error(f"Failed to find all records [{cls.__name__}]: {e}")
            raise DatabaseError(f"Failed to find all records: {e}")
    
    @classmethod
    def find_by_condition(cls, conditions: Dict[str, Any], 
                         limit: Optional[int] = None, 
                         order_by: Optional[str] = None) -> List['BaseModel']:
        """Find records by conditions"""
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
            logging.error(f"Conditional search failed [{cls.__name__}]: {e}")
            raise DatabaseError(f"Conditional search failed: {e}")
    
    @classmethod
    def count(cls, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count number of records"""
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
            logging.error(f"Failed to count records [{cls.__name__}]: {e}")
            raise DatabaseError(f"Failed to count records: {e}")
    
    def save(self) -> bool:
        """Save record (insert or update)"""
        try:
            pk_value = getattr(self, self._primary_key, None)
            
            if pk_value and self.find_by_id(pk_value):
                return self._update()
            else:
                return self._insert()
                
        except Exception as e:
            self.logger.error(f"Failed to save record: {e}")
            raise DatabaseError(f"Failed to save record: {e}")
    
    def _insert(self) -> bool:
        """Insert new record"""
        data = self._get_data_dict()
        
        # Exclude primary key (if auto-increment)
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
        """Update record"""
        data = self._get_data_dict()
        pk_value = data.pop(self._primary_key)
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {self._table_name} SET {set_clause} WHERE {self._primary_key} = %s"
        
        params = tuple(list(data.values()) + [pk_value])
        affected_rows = execute_update(query, params)
        return affected_rows > 0
    
    def delete(self) -> bool:
        """Delete record"""
        try:
            pk_value = getattr(self, self._primary_key)
            if not pk_value:
                raise ValueError("Cannot delete: missing primary key value")
            
            query = f"DELETE FROM {self._table_name} WHERE {self._primary_key} = %s"
            affected_rows = execute_update(query, (pk_value,))
            return affected_rows > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete record: {e}")
            raise DatabaseError(f"Failed to delete record: {e}")
    
    def _get_data_dict(self) -> Dict[str, Any]:
        """Get model data dictionary"""
        return {field: getattr(self, field, None) for field in self._fields}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self._get_data_dict()
    
    def __repr__(self) -> str:
        """String representation"""
        pk_value = getattr(self, self._primary_key, 'Unknown')
        return f"<{self.__class__.__name__}({self._primary_key}={pk_value})>" 