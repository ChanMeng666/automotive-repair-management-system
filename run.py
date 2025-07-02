"""
应用入口点
汽车维修管理系统 - 重构版本
"""
import os
import logging
from app import create_app
from app.utils.database import db_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    # 创建应用
    app = create_app()
    
    # 初始化数据库连接
    with app.app_context():
        db_manager.init_app(app)
    
    # 获取运行配置
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = app.config.get('DEBUG', False)
    
    print("\n" + "="*60)
    print("🚗 Selwyn Panel Beaters Online Service")
    print("汽车维修管理系统 - 重构版本")
    print("="*60)
    print(f"🌐 应用地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"📊 环境: {app.config.get('ENV', 'development')}")
    print("="*60 + "\n")
    
    # 启动应用
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 应用已关闭")
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}")


if __name__ == "__main__":
    main() 