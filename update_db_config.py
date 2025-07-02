#!/usr/bin/env python3
"""
数据库配置更新脚本
用于更新PythonAnywhere部署的数据库连接配置
"""

import os
import sys


def update_connect_py(username, password):
    """更新connect.py文件的数据库配置"""
    
    connect_content = f'''# Database configuration for PythonAnywhere
# 这个文件用于兼容旧的app.py文件中的数据库连接

# PythonAnywhere MySQL 数据库配置
dbhost = '{username}.mysql.pythonanywhere-services.com'
dbuser = '{username}'
dbpass = '{password}'
dbname = '{username}$spb'

# 注意：
# 1. dbhost 格式：用户名.mysql.pythonanywhere-services.com
# 2. dbname 格式：用户名$spb
# 3. dbuser 就是你的PythonAnywhere用户名
# 4. dbpass 是你在PythonAnywhere数据库页面设置的密码
'''
    
    try:
        with open('connect.py', 'w', encoding='utf-8') as f:
            f.write(connect_content)
        print(f"✅ connect.py 配置已更新")
        print(f"   数据库主机: {username}.mysql.pythonanywhere-services.com")
        print(f"   数据库用户: {username}")
        print(f"   数据库名称: {username}$spb")
        return True
    except Exception as e:
        print(f"❌ 更新connect.py失败: {e}")
        return False


def update_wsgi_py(username):
    """更新wsgi.py文件的项目路径"""
    
    wsgi_content = f'''#!/usr/bin/env python3.10
"""
WSGI配置文件 - 用于PythonAnywhere部署
汽车维修管理系统
"""

import sys
import os

# 添加项目路径到Python路径
project_home = '/home/{username}/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = '{username}.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = '{username}'
os.environ['DB_NAME'] = '{username}$spb'

# 导入Flask应用
# 选择一种导入方式：

# 方式1：使用重构后的应用工厂模式（推荐）
from app import create_app
application = create_app('production')

# 方式2：如果要使用旧的app.py文件，注释掉上面两行，取消下面的注释
# from app import app as application

if __name__ == "__main__":
    application.run()
'''
    
    try:
        with open('wsgi.py', 'w', encoding='utf-8') as f:
            f.write(wsgi_content)
        print(f"✅ wsgi.py 配置已更新")
        print(f"   项目路径: /home/{username}/automotive-repair-management-system")
        return True
    except Exception as e:
        print(f"❌ 更新wsgi.py失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 PythonAnywhere 数据库配置更新工具")
    print("=" * 50)
    
    # 获取用户输入
    username = input("请输入你的PythonAnywhere用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        sys.exit(1)
    
    password = input("请输入你的MySQL数据库密码: ").strip()
    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)
    
    print(f"\n📝 配置信息:")
    print(f"   用户名: {username}")
    print(f"   数据库: {username}$spb")
    print(f"   主机: {username}.mysql.pythonanywhere-services.com")
    
    confirm = input("\n确认更新配置？(y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 取消更新")
        sys.exit(0)
    
    print("\n🔄 开始更新配置文件...")
    
    # 更新配置文件
    success = True
    success &= update_connect_py(username, password)
    success &= update_wsgi_py(username)
    
    if success:
        print("\n🎉 配置更新完成！")
        print("\n📋 下一步操作:")
        print("1. 将项目代码上传到PythonAnywhere")
        print("2. 在PythonAnywhere创建数据库")
        print("3. 导入数据库架构（spb_local.sql）")
        print("4. 配置Web应用")
        print("5. 复制wsgi.py内容到PythonAnywhere的WSGI配置文件")
        print("\n📚 详细步骤请参考 PYTHONANYWHERE_DEPLOYMENT_GUIDE.md")
    else:
        print("\n❌ 配置更新失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main() 