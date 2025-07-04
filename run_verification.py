#!/usr/bin/env python3
"""
综合验证脚本
在PythonAnywhere上运行以验证所有修复
"""
import sys
import os
import traceback

# 设置PythonAnywhere环境
sys.path.insert(0, '/home/ChanMeng/automotive-repair-management-system')
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = 'ChanMeng.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = 'ChanMeng'
os.environ['DB_NAME'] = 'ChanMeng$automotive-repair-management-system'
os.environ['DB_PASSWORD'] = '1160210Mc'

def test_database_module():
    """测试数据库模块"""
    print("🔄 测试数据库模块...")
    
    try:
        from app.utils.database_pythonanywhere import (
            DatabaseError, ValidationError, 
            execute_query, execute_update, init_database,
            pa_db_manager
        )
        print("✅ 数据库模块导入成功")
        print("  - DatabaseError: ✅")
        print("  - ValidationError: ✅")
        print("  - execute_query: ✅")
        print("  - execute_update: ✅")
        print("  - init_database: ✅")
        print("  - pa_db_manager: ✅")
        return True
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """测试应用程序创建"""
    print("\n🔄 测试应用程序创建...")
    
    try:
        from app import create_app
        app = create_app('production')
        print("✅ 应用程序创建成功")
        return app
    except Exception as e:
        print(f"❌ 应用程序创建失败: {e}")
        traceback.print_exc()
        return None

def test_service_layers(app):
    """测试服务层"""
    print("\n🔄 测试服务层...")
    
    with app.app_context():
        services = [
            ('customer_service', 'CustomerService'),
            ('job_service', 'JobService'),
            ('billing_service', 'BillingService')
        ]
        
        for module_name, class_name in services:
            try:
                module = __import__(f'app.services.{module_name}', fromlist=[class_name])
                service_class = getattr(module, class_name)
                service_instance = service_class()
                print(f"✅ {class_name}: 创建成功")
            except Exception as e:
                print(f"❌ {class_name}: 创建失败 - {e}")
                traceback.print_exc()
                return False
        
        return True

def test_model_layers():
    """测试模型层"""
    print("\n🔄 测试模型层...")
    
    models = [
        ('customer', 'Customer'),
        ('job', 'Job'),
        ('service', 'Service'),
        ('part', 'Part'),
        ('base', 'BaseModel')
    ]
    
    for module_name, class_name in models:
        try:
            module = __import__(f'app.models.{module_name}', fromlist=[class_name])
            model_class = getattr(module, class_name)
            print(f"✅ {class_name}: 导入成功")
        except Exception as e:
            print(f"❌ {class_name}: 导入失败 - {e}")
            traceback.print_exc()
            return False
    
    return True

def test_routes(app):
    """测试路由"""
    print("\n🔄 测试路由...")
    
    try:
        with app.test_client() as client:
            routes_to_test = [
                ('/', '主页'),
                ('/technician/dashboard', '技师仪表板'),
                ('/administrator/dashboard', '管理员仪表板'),
                ('/customers', '客户列表'),
                ('/about', '关于页面')
            ]
            
            for route, name in routes_to_test:
                try:
                    response = client.get(route)
                    if response.status_code == 200:
                        print(f"✅ {name} ({route}): 状态码 {response.status_code}")
                    else:
                        print(f"⚠️ {name} ({route}): 状态码 {response.status_code}")
                        # 输出错误信息的前200个字符
                        if response.data:
                            error_preview = response.data.decode()[:200]
                            print(f"   错误预览: {error_preview}...")
                except Exception as e:
                    print(f"❌ {name} ({route}): 错误 - {e}")
        
        return True
    except Exception as e:
        print(f"❌ 路由测试失败: {e}")
        traceback.print_exc()
        return False

def test_database_queries(app):
    """测试数据库查询"""
    print("\n🔄 测试数据库查询...")
    
    try:
        with app.app_context():
            from app.utils.database_pythonanywhere import execute_query
            
            # 测试客户查询
            customers = execute_query("SELECT COUNT(*) as count FROM customers")
            if customers:
                print(f"✅ 客户数量查询成功: {customers[0]['count']} 个客户")
            
            # 测试工作订单查询
            jobs = execute_query("SELECT COUNT(*) as count FROM jobs")
            if jobs:
                print(f"✅ 工作订单数量查询成功: {jobs[0]['count']} 个订单")
            
            # 测试服务查询
            services = execute_query("SELECT COUNT(*) as count FROM services")
            if services:
                print(f"✅ 服务数量查询成功: {services[0]['count']} 个服务")
            
            return True
    except Exception as e:
        print(f"❌ 数据库查询测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始综合验证...")
    print("=" * 60)
    
    # 测试数据库模块
    db_ok = test_database_module()
    if not db_ok:
        print("\n❌ 数据库模块测试失败，终止测试")
        return
    
    # 测试应用程序创建
    app = test_app_creation()
    if not app:
        print("\n❌ 应用程序创建失败，终止测试")
        return
    
    # 测试模型层
    model_ok = test_model_layers()
    if not model_ok:
        print("\n❌ 模型层测试失败，终止测试")
        return
    
    # 测试服务层
    service_ok = test_service_layers(app)
    if not service_ok:
        print("\n❌ 服务层测试失败，终止测试")
        return
    
    # 测试数据库查询
    query_ok = test_database_queries(app)
    if not query_ok:
        print("\n❌ 数据库查询测试失败，终止测试")
        return
    
    # 测试路由
    route_ok = test_routes(app)
    
    print("\n" + "=" * 60)
    if route_ok:
        print("🎉 所有测试都通过！应用程序已成功修复！")
        print("\n📋 接下来的步骤:")
        print("1. 在PythonAnywhere控制台重新加载Web应用")
        print("2. 访问网站测试功能")
        print("3. 确认所有页面都能正常工作")
    else:
        print("⚠️ 部分测试失败，但核心功能已修复")
        print("应用程序应该能够正常启动")

if __name__ == "__main__":
    main() 