"""
PythonAnywhere优化的数据库连接管理模块
适用于PythonAnywhere的MySQL连接限制
"""
import mysql.connector
from mysql.connector import Error
from flask import current_app
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import time

class PythonAnywhereDatabase:
    """PythonAnywhere优化的数据库管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_config = None
    
    def init_app(self, app):
        """初始化数据库连接配置"""
        try:
            # 简化的连接配置，不使用连接池
            self.connection_config = {
                'host': app.config['DB_HOST'],
                'port': app.config['DB_PORT'],
                'database': app.config['DB_NAME'],
                'user': app.config['DB_USER'],
                'password': app.config['DB_PASSWORD'],
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False,
                'connection_timeout': 30,
                'auth_plugin': 'mysql_native_password'
            }
            
            # 测试连接
            self._test_connection()
            self.logger.info("数据库连接配置成功")
            
        except Error as e:
            self.logger.error(f"数据库连接配置失败: {e}")
            raise
    
    def _test_connection(self):
        """测试数据库连接"""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            if conn.is_connected():
                self.logger.info("数据库连接测试成功")
                conn.close()
            else:
                raise Error("数据库连接测试失败")
        except Error as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            raise
    
    def get_connection(self):
        """获取数据库连接"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = mysql.connector.connect(**self.connection_config)
                if conn.is_connected():
                    return conn
                else:
                    raise Error("无法建立数据库连接")
            except Error as e:
                self.logger.warning(f"连接尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待1秒后重试
                else:
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
            if conn and conn.is_connected():
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
            if conn and conn.is_connected():
                conn.close()


class DatabaseError(Exception):
    """自定义数据库异常"""
    pass


class ValidationError(Exception):
    """数据验证异常"""
    pass


# 全局数据库管理器实例
pa_db_manager = PythonAnywhereDatabase()

def execute_query(query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Optional[Any]:
    """执行查询操作"""
    try:
        with pa_db_manager.get_cursor() as cursor:
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchone() if fetch_one else cursor.fetchall()
            return None
            
    except Error as e:
        logging.error(f"查询执行失败: {e}")
        raise

def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """执行更新操作"""
    try:
        with pa_db_manager.transaction() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
            
    except Error as e:
        logging.error(f"更新操作失败: {e}")
        raise

def init_database(app):
    """初始化数据库连接"""
    pa_db_manager.init_app(app) 