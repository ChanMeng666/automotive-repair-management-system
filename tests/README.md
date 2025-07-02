# 汽车维修管理系统测试框架

## 📋 概述

本测试框架为汽车维修管理系统提供全面的测试覆盖，包括单元测试、集成测试、安全测试等。采用pytest作为测试运行器，支持模拟测试、覆盖率检查和持续集成。

## 🏗️ 测试结构

```
tests/
├── __init__.py                 # 测试模块初始化
├── conftest.py                 # pytest配置和fixture
├── utils.py                    # 测试工具和辅助函数
├── README.md                   # 测试文档
├── unit/                       # 单元测试
│   ├── test_basic.py          # 基础功能测试
│   ├── test_security.py       # 安全模块测试
│   ├── test_models.py         # 模型层测试
│   └── test_services.py       # 服务层测试
├── integration/                # 集成测试
│   ├── test_views.py          # 视图层集成测试
│   ├── test_api.py            # API集成测试
│   └── test_database.py       # 数据库集成测试
└── fixtures/                   # 测试数据和fixture
    ├── sample_data.json       # 示例数据
    └── test_config.py         # 测试配置
```

## 🚀 快速开始

### 安装依赖

```bash
pip install pytest pytest-cov pytest-mock
```

### 运行测试

#### 使用测试脚本（推荐）

```bash
# 检查测试结构
python run_tests.py --check

# 运行单元测试
python run_tests.py --unit

# 运行集成测试
python run_tests.py --integration

# 运行安全测试
python run_tests.py --security

# 运行所有测试
python run_tests.py --all

# 运行覆盖率测试
python run_tests.py --coverage
```

#### 直接使用pytest

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v

# 运行安全相关测试
pytest tests/ -m security -v

# 运行覆盖率测试
pytest tests/ --cov=app --cov-report=html
```

## 🏷️ 测试标记

测试使用pytest标记进行分类：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.security` - 安全测试
- `@pytest.mark.slow` - 慢速测试

## 🧪 测试类型

### 单元测试

测试单个模块、类或函数的功能：

- **安全模块测试** (`test_security.py`)
  - 密码哈希和验证
  - 输入清理和验证
  - SQL注入防护
  - CSRF保护
  - 会话安全

- **模型层测试** (`test_models.py`)
  - 数据模型CRUD操作
  - 业务逻辑验证
  - 数据验证规则

- **服务层测试** (`test_services.py`)
  - 业务服务逻辑
  - 数据处理流程
  - 错误处理

### 集成测试

测试模块间的交互和系统功能：

- **视图层测试** (`test_views.py`)
  - 路由功能
  - 请求处理
  - 响应验证
  - 权限控制

- **API测试** (`test_api.py`)
  - RESTful API功能
  - 数据序列化
  - 错误响应

- **数据库测试** (`test_database.py`)
  - 数据库连接
  - 事务处理
  - 数据一致性

## 🛠️ 测试工具

### Fixtures

`conftest.py`中定义的测试装置：

- `app` - Flask应用实例
- `client` - 测试客户端
- `mock_db_manager` - 模拟数据库管理器
- `sample_*_data` - 示例数据
- `authenticated_session` - 已认证会话
- `admin_session` - 管理员会话

### 测试工具函数

`utils.py`中提供的辅助函数：

- `create_mock_*()` - 创建模拟对象
- `assert_json_response()` - 断言JSON响应
- `assert_redirect_response()` - 断言重定向响应
- `MockDatabaseCursor` - 模拟数据库游标
- `TestResponseHelper` - 响应断言辅助类

## 📊 覆盖率报告

运行覆盖率测试后，会在`htmlcov/`目录生成HTML报告：

```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # 打开覆盖率报告
```

## ⚙️ 配置

### pytest.ini

项目根目录的pytest配置文件：

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
```

### 测试配置

在`conftest.py`中定义的测试配置：

- 禁用CSRF保护
- 使用测试数据库
- 减少日志输出
- 模拟外部依赖

## 🔧 编写测试指南

### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestCustomerService:
    def test_create_customer(self, mock_db_manager):
        """测试创建客户"""
        # 准备测试数据
        customer_data = {
            'first_name': '张',
            'last_name': '三',
            'email': 'zhangsan@example.com'
        }
        
        # 模拟数据库返回
        mock_db_manager.execute_update.return_value = 1
        
        # 执行测试
        from app.services.customer_service import CustomerService
        service = CustomerService()
        result = service.create_customer(customer_data)
        
        # 验证结果
        assert result == 1
        mock_db_manager.execute_update.assert_called_once()
```

### 集成测试示例

```python
@pytest.mark.integration
class TestCustomerAPI:
    def test_create_customer_api(self, client, authenticated_session):
        """测试创建客户API"""
        customer_data = {
            'first_name': '李',
            'last_name': '四',
            'email': 'lisi@example.com',
            'csrf_token': 'test_token'
        }
        
        response = authenticated_session.post('/api/customers', 
                                           data=customer_data)
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'customer_id' in data
```

## 🚨 测试最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 遵循`test_<功能>_<场景>`模式
- 例如：`test_create_customer_with_valid_data`

### 2. 测试结构

- **Arrange** - 准备测试数据和环境
- **Act** - 执行被测试的功能
- **Assert** - 验证结果

### 3. 模拟和隔离

- 使用Mock隔离外部依赖
- 避免实际的数据库操作
- 模拟网络请求和文件操作

### 4. 数据清理

- 在测试后清理临时数据
- 使用fixture管理测试状态
- 确保测试间的独立性

### 5. 断言明确性

- 使用具体的断言
- 提供清晰的错误信息
- 验证预期的副作用

## 🐛 调试测试

### 运行特定测试

```bash
# 运行特定测试文件
pytest tests/unit/test_security.py -v

# 运行特定测试类
pytest tests/unit/test_security.py::TestPasswordSecurity -v

# 运行特定测试方法
pytest tests/unit/test_security.py::TestPasswordSecurity::test_hash_password -v
```

### 调试输出

```bash
# 显示打印输出
pytest tests/ -v -s

# 显示详细错误信息
pytest tests/ -v --tb=long

# 在第一个失败时停止
pytest tests/ -v -x
```

## 📈 持续集成

### GitHub Actions配置示例

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python run_tests.py --all
    - name: Generate coverage report
      run: |
        python run_tests.py --coverage
```

## 📚 相关资源

- [pytest官方文档](https://docs.pytest.org/)
- [pytest-cov插件](https://pytest-cov.readthedocs.io/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)
- [Flask测试文档](https://flask.palletsprojects.com/en/2.0.x/testing/) 