# PythonAnywhere 部署指南
## 汽车维修管理系统部署到PythonAnywhere

本指南将详细说明如何将汽车维修管理系统部署到PythonAnywhere平台，包括数据库配置、文件上传和环境设置。

## 📋 部署前准备

### 1. PythonAnywhere账户准备
- 注册PythonAnywhere账户：https://www.pythonanywhere.com/
- 选择合适的套餐（免费账户有一定限制）
- 登录到PythonAnywhere控制面板

### 2. 项目文件准备
确保你的项目包含以下关键文件：
- `requirements.txt` - 依赖包列表
- `wsgi.py` - WSGI配置文件
- `connect.py` - 数据库连接配置
- `spb_local.sql` - 数据库架构文件

## 🚀 部署步骤

### 步骤1：上传项目文件

#### 方式A：通过Git克隆（推荐）
1. 打开PythonAnywhere的Bash控制台
2. 运行以下命令：
```bash
cd ~
git clone https://github.com/yourusername/automotive-repair-management-system.git
cd automotive-repair-management-system
```

#### 方式B：通过文件上传
1. 在PythonAnywhere的Files标签页中创建项目目录
2. 将项目文件逐个上传到 `/home/yourusername/automotive-repair-management-system/`

### 步骤2：配置数据库

#### 2.1 创建MySQL数据库
1. 登录PythonAnywhere控制面板
2. 点击"Databases"标签
3. 在MySQL部分，设置数据库密码（如果还没有设置）
4. 创建新数据库，命名为：`yourusername$spb`
   - 注意：数据库名格式必须是 `用户名$数据库名`

#### 2.2 导入数据库架构
1. 在Databases页面，点击"Open MySQL console"
2. 选择你创建的数据库 `yourusername$spb`
3. 复制 `spb_local.sql` 文件的内容并执行
4. 或者使用命令行：
```bash
mysql -u yourusername -p'your_password' -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb < spb_local.sql
```

#### 2.3 更新数据库连接配置
编辑 `connect.py` 文件，更新以下配置：
```python
# 替换为你的实际信息
dbhost = 'yourusername.mysql.pythonanywhere-services.com'
dbuser = 'yourusername'  # 你的PythonAnywhere用户名
dbpass = 'your_database_password'  # 你设置的数据库密码
dbname = 'yourusername$spb'  # 你的数据库名
```

### 步骤3：安装Python依赖

1. 在Bash控制台中，进入项目目录：
```bash
cd ~/automotive-repair-management-system
```

2. 创建虚拟环境（可选但推荐）：
```bash
python3.10 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

### 步骤4：配置Web应用

#### 4.1 创建Web应用
1. 在PythonAnywhere控制面板，点击"Web"标签
2. 点击"Add a new web app"
3. 选择你的域名（免费用户：yourusername.pythonanywhere.com）
4. 选择"Manual configuration"
5. 选择Python版本（推荐Python 3.10）

#### 4.2 配置WSGI文件
1. 在Web标签页中，找到"Code"部分
2. 点击WSGI配置文件链接（通常是 `/var/www/yourusername_pythonanywhere_com_wsgi.py`）
3. 删除所有内容，替换为以下内容：

```python
#!/usr/bin/env python3.10

import sys
import os

# 添加项目路径
project_home = '/home/yourusername/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'

# 导入Flask应用
from app import create_app
application = create_app('production')
```

#### 4.3 配置虚拟环境（如果使用）
在Web配置页面的"Virtualenv"部分，输入：
```
/home/yourusername/automotive-repair-management-system/venv
```

#### 4.4 配置静态文件
在"Static files"部分添加：
- URL: `/static/`
- Directory: `/home/yourusername/automotive-repair-management-system/app/static/`

### 步骤5：环境变量配置

在WSGI文件中或者通过PythonAnywhere的环境变量设置：
```python
os.environ['SECRET_KEY'] = 'your-production-secret-key'
os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_PASSWORD'] = 'your_database_password'
os.environ['DB_NAME'] = 'yourusername$spb'
```

### 步骤6：测试和启动

1. 在Web配置页面，点击"Reload"按钮
2. 访问你的域名：`https://yourusername.pythonanywhere.com`
3. 检查是否正常运行

## 🔧 故障排除

### 常见问题和解决方案

#### 1. 500内部服务器错误
- 检查错误日志：Web标签页 → Error log
- 确认所有依赖包已安装
- 检查WSGI文件配置是否正确
- 验证数据库连接配置

#### 2. 数据库连接失败
- 确认数据库名格式：`yourusername$spb`
- 检查数据库密码是否正确
- 确认数据库主机地址格式

#### 3. 静态文件无法加载
- 检查静态文件路径配置
- 确认文件权限设置正确

#### 4. 模块导入错误
- 检查项目路径是否正确添加到sys.path
- 确认所有必要的依赖包已安装

### 调试命令

在Bash控制台中：
```bash
# 检查Python路径
python3.10 -c "import sys; print('\n'.join(sys.path))"

# 测试数据库连接
python3.10 -c "import mysql.connector; print('MySQL connector available')"

# 检查Flask应用
cd ~/automotive-repair-management-system
python3.10 -c "from app import create_app; app = create_app('production'); print('App created successfully')"
```

## 📝 重要注意事项

1. **安全性**：
   - 生产环境中使用强密码
   - 设置复杂的SECRET_KEY
   - 定期更新依赖包

2. **性能优化**：
   - 免费账户有CPU秒数限制
   - 考虑升级到付费账户以获得更好性能

3. **备份**：
   - 定期备份数据库
   - 保持GitHub仓库更新

4. **监控**：
   - 定期检查错误日志
   - 监控应用性能

## 🔄 更新部署

当你需要更新应用时：
```bash
cd ~/automotive-repair-management-system
git pull origin main
pip install -r requirements.txt
```
然后在Web标签页点击"Reload"按钮。

## 📞 支持

如果遇到问题：
1. 查看PythonAnywhere帮助文档
2. 检查项目的GitHub Issues
3. 查看PythonAnywhere论坛
4. 联系PythonAnywhere支持团队

---

**注意**：请将所有的 `yourusername` 替换为你的实际PythonAnywhere用户名，将 `your_database_password` 替换为你的实际数据库密码。 