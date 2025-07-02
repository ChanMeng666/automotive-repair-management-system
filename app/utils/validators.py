"""
输入验证工具
"""
import re
from datetime import datetime, date
from typing import Optional, Any
import html


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否有效
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
    
    Returns:
        是否有效
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # 移除空格和连字符
    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # 检查是否为10-11位数字
    pattern = r'^\d{10,11}$'
    return bool(re.match(pattern, clean_phone))


def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    验证日期格式
    
    Args:
        date_str: 日期字符串
        format_str: 日期格式
    
    Returns:
        是否有效
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    try:
        datetime.strptime(date_str.strip(), format_str)
        return True
    except ValueError:
        return False


def validate_positive_number(value: Any) -> bool:
    """
    验证正数
    
    Args:
        value: 数值
    
    Returns:
        是否为正数
    """
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_positive_integer(value: Any) -> bool:
    """
    验证正整数
    
    Args:
        value: 数值
    
    Returns:
        是否为正整数
    """
    try:
        num = int(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_string_length(text: str, min_length: int = 1, max_length: int = 255) -> bool:
    """
    验证字符串长度
    
    Args:
        text: 文本
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        是否在有效长度范围内
    """
    if not isinstance(text, str):
        return False
    
    length = len(text.strip())
    return min_length <= length <= max_length


def sanitize_input(value: Any) -> str:
    """
    清理输入数据
    
    Args:
        value: 输入值
    
    Returns:
        清理后的字符串
    """
    if value is None:
        return ""
    
    # 转换为字符串
    text = str(value)
    
    # HTML转义
    text = html.escape(text)
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def validate_name(name: str) -> bool:
    """
    验证姓名格式
    
    Args:
        name: 姓名
    
    Returns:
        是否有效
    """
    if not name or not isinstance(name, str):
        return False
    
    # 姓名应该只包含字母、空格、连字符和撇号
    pattern = r"^[a-zA-Z\s\-']{1,50}$"
    return bool(re.match(pattern, name.strip()))


def validate_service_part_name(name: str) -> bool:
    """
    验证服务或零件名称
    
    Args:
        name: 名称
    
    Returns:
        是否有效
    """
    if not name or not isinstance(name, str):
        return False
    
    # 服务/零件名称可以包含字母、数字、空格、连字符和括号
    pattern = r"^[a-zA-Z0-9\s\-()]{1,100}$"
    return bool(re.match(pattern, name.strip()))


def validate_cost(cost: Any) -> bool:
    """
    验证成本/价格
    
    Args:
        cost: 成本值
    
    Returns:
        是否有效
    """
    try:
        value = float(cost)
        # 成本应该为非负数，且不超过合理上限
        return 0 <= value <= 999999.99
    except (ValueError, TypeError):
        return False


def validate_quantity(quantity: Any) -> bool:
    """
    验证数量
    
    Args:
        quantity: 数量值
    
    Returns:
        是否有效
    """
    try:
        value = int(quantity)
        # 数量应该为正整数，且不超过合理上限
        return 1 <= value <= 1000
    except (ValueError, TypeError):
        return False


def validate_date_not_past(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    验证日期不能是过去的日期
    
    Args:
        date_str: 日期字符串
        format_str: 日期格式
    
    Returns:
        是否有效（不是过去的日期）
    """
    if not validate_date(date_str, format_str):
        return False
    
    try:
        input_date = datetime.strptime(date_str.strip(), format_str).date()
        return input_date >= date.today()
    except ValueError:
        return False


class ValidationResult:
    """验证结果类"""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
    
    def add_error(self, field: str, message: str):
        """添加错误"""
        self.is_valid = False
        self.errors.append(f"{field}: {message}")
    
    def get_errors(self) -> list:
        """获取错误列表"""
        return self.errors


def validate_customer_data(data: dict) -> ValidationResult:
    """
    验证客户数据
    
    Args:
        data: 客户数据字典
    
    Returns:
        验证结果
    """
    result = ValidationResult()
    
    # 验证姓氏
    family_name = data.get('family_name', '')
    if not family_name or not family_name.strip():
        result.add_error('family_name', '姓氏不能为空')
    elif not validate_name(family_name):
        result.add_error('family_name', '姓氏格式无效')
    
    # 验证名字（可选）
    first_name = data.get('first_name', '')
    if first_name and not validate_name(first_name):
        result.add_error('first_name', '名字格式无效')
    
    # 验证邮箱
    email = data.get('email', '')
    if not email or not email.strip():
        result.add_error('email', '邮箱不能为空')
    elif not validate_email(email):
        result.add_error('email', '邮箱格式无效')
    
    # 验证手机号
    phone = data.get('phone', '')
    if not phone or not phone.strip():
        result.add_error('phone', '手机号不能为空')
    elif not validate_phone(phone):
        result.add_error('phone', '手机号格式无效')
    
    return result


def validate_service_data(data: dict) -> ValidationResult:
    """
    验证服务数据
    
    Args:
        data: 服务数据字典
    
    Returns:
        验证结果
    """
    result = ValidationResult()
    
    # 验证服务名称
    service_name = data.get('service_name', '')
    if not service_name or not service_name.strip():
        result.add_error('service_name', '服务名称不能为空')
    elif not validate_service_part_name(service_name):
        result.add_error('service_name', '服务名称格式无效')
    
    # 验证成本
    cost = data.get('cost')
    if cost is None:
        result.add_error('cost', '成本不能为空')
    elif not validate_cost(cost):
        result.add_error('cost', '成本必须为有效的正数')
    
    return result


def validate_part_data(data: dict) -> ValidationResult:
    """
    验证零件数据
    
    Args:
        data: 零件数据字典
    
    Returns:
        验证结果
    """
    result = ValidationResult()
    
    # 验证零件名称
    part_name = data.get('part_name', '')
    if not part_name or not part_name.strip():
        result.add_error('part_name', '零件名称不能为空')
    elif not validate_service_part_name(part_name):
        result.add_error('part_name', '零件名称格式无效')
    
    # 验证成本
    cost = data.get('cost')
    if cost is None:
        result.add_error('cost', '成本不能为空')
    elif not validate_cost(cost):
        result.add_error('cost', '成本必须为有效的正数')
    
    return result 