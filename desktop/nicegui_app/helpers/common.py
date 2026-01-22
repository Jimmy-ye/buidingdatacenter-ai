"""
通用辅助函数模块

提供可复用的工具函数和常量

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Optional


def parse_float(value: Any) -> Optional[float]:
    """
    安全地解析浮点数

    Args:
        value: 输入值（可以是字符串、数字等）

    Returns:
        解析后的浮点数，如果解析失败则返回 None
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None
    return None


def format_float(value: Any, decimals: int = 2) -> str:
    """
    格式化浮点数为字符串

    Args:
        value: 输入值
        decimals: 小数位数，默认为 2

    Returns:
        格式化后的字符串，如果无法格式化则返回空字符串
    """
    parsed = parse_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{decimals}f}"


def safe_dict_get(data: Any, key: str, default: Any = None) -> Any:
    """
    安全地从字典获取值

    Args:
        data: 输入数据（可以是字典或其他）
        key: 键名
        default: 默认值

    Returns:
        字典中的值或默认值
    """
    if isinstance(data, dict):
        return data.get(key, default)
    return default


# ==================== 便捷函数 ====================

def parse_number(value: Any) -> Optional[float]:
    """
    解析数字（parse_float 的别名）

    Args:
        value: 输入值

    Returns:
        解析后的浮点数
    """
    return parse_float(value)


def format_number(value: Any, decimals: int = 2) -> str:
    """
    格式化数字（format_float 的别名）

    Args:
        value: 输入值
        decimals: 小数位数

    Returns:
        格式化后的字符串
    """
    return format_float(value, decimals)
