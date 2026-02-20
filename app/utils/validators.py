"""
Input Validation Utilities
"""
import re
from datetime import datetime, date
from typing import Optional, Any
import html


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        Whether the email is valid
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number

    Returns:
        Whether the phone number is valid
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove spaces and hyphens
    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

    # Check if it's 10-11 digits
    pattern = r'^\d{10,11}$'
    return bool(re.match(pattern, clean_phone))


def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    Validate date format.

    Args:
        date_str: Date string
        format_str: Date format

    Returns:
        Whether the date is valid
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
    Validate positive number.

    Args:
        value: Numeric value

    Returns:
        Whether the value is a positive number
    """
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_positive_integer(value: Any) -> bool:
    """
    Validate positive integer.

    Args:
        value: Numeric value

    Returns:
        Whether the value is a positive integer
    """
    try:
        num = int(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_string_length(text: str, min_length: int = 1, max_length: int = 255) -> bool:
    """
    Validate string length.

    Args:
        text: Text string
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        Whether the length is within the valid range
    """
    if not isinstance(text, str):
        return False

    length = len(text.strip())
    return min_length <= length <= max_length


def sanitize_input(value: Any) -> str:
    """
    Sanitize input data.

    Args:
        value: Input value

    Returns:
        Sanitized string
    """
    if value is None:
        return ""

    # Convert to string
    text = str(value)

    # HTML escape
    text = html.escape(text)

    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def validate_name(name: str) -> bool:
    """
    Validate name format.

    Args:
        name: Name string

    Returns:
        Whether the name is valid
    """
    if not name or not isinstance(name, str):
        return False

    # Names should only contain letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']{1,50}$"
    return bool(re.match(pattern, name.strip()))


def validate_service_part_name(name: str) -> bool:
    """
    Validate service or part name.

    Args:
        name: Name string

    Returns:
        Whether the name is valid
    """
    if not name or not isinstance(name, str):
        return False

    # Service/part names can contain letters, numbers, spaces, hyphens, and parentheses
    pattern = r"^[a-zA-Z0-9\s\-()]{1,100}$"
    return bool(re.match(pattern, name.strip()))


def validate_cost(cost: Any) -> bool:
    """
    Validate cost/price.

    Args:
        cost: Cost value

    Returns:
        Whether the cost is valid
    """
    try:
        value = float(cost)
        # Cost should be non-negative and not exceed a reasonable upper limit
        return 0 <= value <= 999999.99
    except (ValueError, TypeError):
        return False


def validate_quantity(quantity: Any) -> bool:
    """
    Validate quantity.

    Args:
        quantity: Quantity value

    Returns:
        Whether the quantity is valid
    """
    try:
        value = int(quantity)
        # Quantity should be a positive integer and not exceed a reasonable upper limit
        return 1 <= value <= 1000
    except (ValueError, TypeError):
        return False


def validate_date_not_past(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    Validate that the date is not in the past.

    Args:
        date_str: Date string
        format_str: Date format

    Returns:
        Whether the date is valid (not in the past)
    """
    if not validate_date(date_str, format_str):
        return False

    try:
        input_date = datetime.strptime(date_str.strip(), format_str).date()
        return input_date >= date.today()
    except ValueError:
        return False


class ValidationResult:
    """Validation result container"""

    def __init__(self):
        self.is_valid = True
        self.errors = []

    def add_error(self, field: str, message: str):
        """Add an error"""
        self.is_valid = False
        self.errors.append(f"{field}: {message}")

    def get_errors(self) -> list:
        """Get the list of errors"""
        return self.errors


def validate_customer_data(data: dict) -> ValidationResult:
    """
    Validate customer data.

    Args:
        data: Customer data dictionary

    Returns:
        Validation result
    """
    result = ValidationResult()

    # Validate family name
    family_name = data.get('family_name', '')
    if not family_name or not family_name.strip():
        result.add_error('family_name', 'Family name is required')
    elif not validate_name(family_name):
        result.add_error('family_name', 'Invalid family name format')

    # Validate first name (optional)
    first_name = data.get('first_name', '')
    if first_name and not validate_name(first_name):
        result.add_error('first_name', 'Invalid first name format')

    # Validate email
    email = data.get('email', '')
    if not email or not email.strip():
        result.add_error('email', 'Email is required')
    elif not validate_email(email):
        result.add_error('email', 'Invalid email format')

    # Validate phone number
    phone = data.get('phone', '')
    if not phone or not phone.strip():
        result.add_error('phone', 'Phone number is required')
    elif not validate_phone(phone):
        result.add_error('phone', 'Invalid phone number format')

    return result


def validate_service_data(data: dict) -> ValidationResult:
    """
    Validate service data.

    Args:
        data: Service data dictionary

    Returns:
        Validation result
    """
    result = ValidationResult()

    # Validate service name
    service_name = data.get('service_name', '')
    if not service_name or not service_name.strip():
        result.add_error('service_name', 'Service name is required')
    elif not validate_service_part_name(service_name):
        result.add_error('service_name', 'Invalid service name format')

    # Validate cost
    cost = data.get('cost')
    if cost is None:
        result.add_error('cost', 'Cost is required')
    elif not validate_cost(cost):
        result.add_error('cost', 'Cost must be a valid positive number')

    return result


def validate_part_data(data: dict) -> ValidationResult:
    """
    Validate part data.

    Args:
        data: Part data dictionary

    Returns:
        Validation result
    """
    result = ValidationResult()

    # Validate part name
    part_name = data.get('part_name', '')
    if not part_name or not part_name.strip():
        result.add_error('part_name', 'Part name is required')
    elif not validate_service_part_name(part_name):
        result.add_error('part_name', 'Invalid part name format')

    # Validate cost
    cost = data.get('cost')
    if cost is None:
        result.add_error('cost', 'Cost is required')
    elif not validate_cost(cost):
        result.add_error('cost', 'Cost must be a valid positive number')

    return result
