# 🚀 PythonAnywhere 快速部署指南

## 简要步骤

### 1. 准备配置文件
在本地运行配置更新脚本：
```bash
python update_db_config.py
```
输入你的PythonAnywhere用户名和数据库密码。

### 2. 上传代码到PythonAnywhere
在PythonAnywhere的Bash控制台中：
```bash
cd ~
git clone https://github.com/yourusername/automotive-repair-management-system.git
cd automotive-repair-management-system
```

### 3. 运行部署脚本
```bash
export PA_USERNAME=你的用户名
bash deploy_to_pythonanywhere.sh
```

### 4. 创建数据库
1. 在PythonAnywhere控制面板，点击"Databases"
2. 创建数据库：`yourusername$spb`
3. 在MySQL控制台中导入架构：
```sql
-- 复制粘贴 spb_local.sql 的内容
```

### 5. 配置Web应用
1. 点击"Web"标签 → "Add a new web app"
2. 选择"Manual configuration" → Python 3.10
3. 设置虚拟环境：`/home/yourusername/automotive-repair-management-system/venv`
4. 复制 `wsgi.py` 内容到WSGI配置文件
5. 配置静态文件：`/static/` → `/home/yourusername/automotive-repair-management-system/app/static/`

### 6. 测试部署
点击"Reload"按钮，然后访问：`https://yourusername.pythonanywhere.com`

## 📁 重要文件

- `PYTHONANYWHERE_DEPLOYMENT_GUIDE.md` - 详细部署指南
- `update_db_config.py` - 配置更新脚本
- `deploy_to_pythonanywhere.sh` - 自动部署脚本
- `wsgi.py` - WSGI配置文件
- `connect.py` - 数据库连接配置

## 🆘 遇到问题？

1. 查看详细部署指南：`PYTHONANYWHERE_DEPLOYMENT_GUIDE.md`
2. 检查PythonAnywhere错误日志
3. 确认数据库配置正确
4. 验证所有依赖包已安装

## 🔗 有用链接

- [PythonAnywhere帮助文档](https://help.pythonanywhere.com/)
- [Flask部署指南](https://flask.palletsprojects.com/en/latest/deploying/)
- [MySQL连接问题排查](https://help.pythonanywhere.com/pages/MySQLdb/) 