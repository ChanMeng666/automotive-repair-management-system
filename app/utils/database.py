"""
数据库连接管理模块
提供数据库连接池、事务管理和异常处理
"""
import mysql.connector
from mysql.connector import pooling, Error
from flask import current_app, g
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.pool = None
        self.logger = logging.getLogger(__name__)
    
    def init_app(self, app):
        """初始化数据库连接池"""
        try:
            pool_config = {
                'pool_name': 'spb_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'host': app.config['DB_HOST'],
                'port': app.config['DB_PORT'],
                'database': app.config['DB_NAME'],
                'user': app.config['DB_USER'],
                'password': app.config['DB_PASSWORD'],
                'autocommit': False,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'raise_on_warnings': True
            }
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            self.logger.info("数据库连接池初始化成功")
            
        except Error as e:
            self.logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    def get_connection(self):
        """从连接池获取连接"""
        try:
            return self.pool.get_connection()
        except Error as e:
            self.logger.error(f"获取数据库连接失败: {e}")
            raise
    
    @contextmanager
    def get_cursor(self, dictionary=True, buffered=True):
        """上下文管理器，自动管理连接和游标"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=dictionary, buffered=buffered)
            yield cursor
        except Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            yield cursor
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"事务执行失败: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db_cursor():
    """获取数据库游标的辅助函数"""
    return db_manager.get_cursor()


def execute_query(query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Optional[Any]:
    """
    执行查询操作
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_one: 是否只返回一条记录
    
    Returns:
        查询结果
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchone() if fetch_one else cursor.fetchall()
            return None
            
    except Error as e:
        logging.error(f"查询执行失败: {e}")
        raise


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """
    执行更新操作
    
    Args:
        query: SQL更新语句
        params: 更新参数
    
    Returns:
        影响的行数
    """
    try:
        with db_manager.transaction() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
            
    except Error as e:
        logging.error(f"更新操作失败: {e}")
        raise


def execute_many(query: str, params_list: List[tuple]) -> int:
    """
    批量执行操作
    
    Args:
        query: SQL语句
        params_list: 参数列表
    
    Returns:
        影响的行数
    """
    try:
        with db_manager.transaction() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
            
    except Error as e:
        logging.error(f"批量操作失败: {e}")
        raise


class DatabaseError(Exception):
    """自定义数据库异常"""
    pass


class ValidationError(Exception):
    """数据验证异常"""
    pass


def init_database(app):
    """初始化数据库连接"""
    db_manager.init_app(app) 