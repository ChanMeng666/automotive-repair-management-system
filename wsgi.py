#!/usr/bin/env python3.10
"""
WSGI配置文件 - 用于PythonAnywhere部署
汽车维修管理系统
"""

import sys
import os

# 添加项目路径到Python路径
project_home = '/home/ChanMeng/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = 'ChanMeng.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = 'ChanMeng'
os.environ['DB_NAME'] = 'ChanMeng$spb'

# 导入Flask应用
# 选择一种导入方式：

# 方式1：使用重构后的应用工厂模式（推荐）
from app import create_app
application = create_app('production')

# 方式2：如果要使用旧的app.py文件，注释掉上面两行，取消下面的注释
# from app import app as application

if __name__ == "__main__":
    application.run()
