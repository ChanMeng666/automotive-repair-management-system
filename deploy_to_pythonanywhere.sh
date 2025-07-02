#!/bin/bash

# PythonAnywhere 自动部署脚本
# 汽车维修管理系统

echo "🚗 开始部署汽车维修管理系统到PythonAnywhere..."

# 配置变量（请根据实际情况修改）
USERNAME="${PA_USERNAME:-yourusername}"
PROJECT_DIR="/home/$USERNAME/automotive-repair-management-system"
VENV_DIR="$PROJECT_DIR/venv"

echo "📂 用户名: $USERNAME"
echo "📁 项目目录: $PROJECT_DIR"

# 检查是否在PythonAnywhere环境中
if [ ! -d "/home/$USERNAME" ]; then
    echo "❌ 错误：请在PythonAnywhere的Bash控制台中运行此脚本"
    exit 1
fi

# 步骤1：进入项目目录
echo "📂 进入项目目录..."
cd "$PROJECT_DIR" || {
    echo "❌ 错误：无法进入项目目录 $PROJECT_DIR"
    echo "请确保已经克隆了项目代码"
    exit 1
}

# 步骤2：创建并激活虚拟环境
echo "🐍 设置Python虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3.10 -m venv "$VENV_DIR"
fi

echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 步骤3：升级pip并安装依赖
echo "📦 安装Python依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 步骤4：检查关键文件
echo "🔍 检查关键文件..."
REQUIRED_FILES=("connect.py" "wsgi.py" "spb_local.sql" "requirements.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "⚠️  警告：缺少文件 $file"
    else
        echo "✅ 找到文件 $file"
    fi
done

# 步骤5：测试应用导入
echo "🧪 测试应用导入..."
python3.10 -c "
try:
    from app import create_app
    app = create_app('production')
    print('✅ Flask应用导入成功')
except Exception as e:
    print(f'❌ Flask应用导入失败: {e}')
    exit(1)
"

# 步骤6：测试数据库连接库
echo "🗄️  测试数据库连接库..."
python3.10 -c "
try:
    import mysql.connector
    print('✅ MySQL连接库可用')
except ImportError:
    print('❌ MySQL连接库不可用')
    exit(1)
"

# 步骤7：显示配置提醒
echo ""
echo "🎉 部署脚本执行完成！"
echo ""
echo "📋 接下来请手动完成以下步骤："
echo ""
echo "1. 📊 配置数据库："
echo "   - 登录PythonAnywhere控制面板"
echo "   - 点击'Databases'标签"
echo "   - 创建数据库：${USERNAME}\$spb"
echo "   - 导入数据库架构：spb_local.sql"
echo ""
echo "2. 🔧 更新connect.py文件："
echo "   编辑 connect.py，更新数据库连接信息："
echo "   dbhost = '${USERNAME}.mysql.pythonanywhere-services.com'"
echo "   dbuser = '${USERNAME}'"
echo "   dbpass = 'your_database_password'"
echo "   dbname = '${USERNAME}\$spb'"
echo ""
echo "3. 🌐 配置Web应用："
echo "   - 在PythonAnywhere点击'Web'标签"
echo "   - 创建新的Web应用（Manual configuration, Python 3.10）"
echo "   - 设置WSGI文件路径"
echo "   - 设置虚拟环境路径：$VENV_DIR"
echo "   - 配置静态文件：/static/ -> $PROJECT_DIR/app/static/"
echo ""
echo "4. 📝 WSGI配置文件内容："
echo "   将wsgi.py的内容复制到PythonAnywhere的WSGI配置文件中"
echo "   并将路径更新为实际路径"
echo ""
echo "5. 🔄 重载Web应用："
echo "   在Web标签页点击'Reload'按钮"
echo ""
echo "6. 🌍 访问应用："
echo "   https://${USERNAME}.pythonanywhere.com"
echo ""
echo "📚 详细说明请参考：PYTHONANYWHERE_DEPLOYMENT_GUIDE.md"
echo ""
echo "✅ 部署准备完成！" 