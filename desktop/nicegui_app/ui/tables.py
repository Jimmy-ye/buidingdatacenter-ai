"""
表格组件模块

提供可复用的表格组件和辅助函数

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta


class AssetTableHelper:
    """
    资产表格辅助类

    提供资产表格的过滤、格式化和更新逻辑
    """

    @staticmethod
    def get_table_columns() -> List[Dict[str, Any]]:
        """
        获取资产表格的列定义

        Returns:
            列定义列表
        """
        return [
            {
                "name": "title",
                "label": "标题",
                "field": "title",
                "sortable": True,
                "style": "max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
            },
            {
                "name": "modality",
                "label": "类型",
                "field": "modality",
                "sortable": True,
                "style": "width: 80px;",
            },
            {
                "name": "short_date",
                "label": "日期",
                "field": "short_date",
                "sortable": True,
                "style": "width: 80px;",
            },
            {
                "name": "keywords",
                "label": "关键词",
                "field": "keywords",
                "style": "width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
            },
        ]

    @staticmethod
    def apply_filters(
        assets: List[Dict[str, Any]],
        modality_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        time_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        应用过滤条件到资产列表

        Args:
            assets: 资产列表
            modality_filter: 模态类型过滤（image/table/text/document等）
            role_filter: 角色过滤（scene_issue/meter/等）
            time_filter: 时间过滤（all/7d/30d）

        Returns:
            过滤后的资产列表
        """
        if not assets:
            return []

        modality_value = modality_filter or ""
        role_value = (role_filter or "").strip().lower()
        time_value = time_filter or "all"

        now = datetime.utcnow()
        cutoff: Optional[datetime] = None
        if time_value == "7d":
            cutoff = now - timedelta(days=7)
        elif time_value == "30d":
            cutoff = now - timedelta(days=30)

        filtered: List[Dict[str, Any]] = []
        for asset in assets:
            # 模态类型过滤
            if modality_value and asset.get("modality") != modality_value:
                continue

            # 角色过滤
            role = (asset.get("content_role") or "").lower()
            if role_value and role != role_value:
                continue

            # 时间过滤
            if cutoff is not None:
                ct_raw = asset.get("capture_time")
                if not ct_raw:
                    continue
                try:
                    ct_str = str(ct_raw)
                    if ct_str.endswith("Z"):
                        ct_str = ct_str.replace("Z", "+00:00")
                    capture_dt = datetime.fromisoformat(ct_str)
                except Exception:
                    continue
                if capture_dt < cutoff:
                    continue

            filtered.append(asset)

        return filtered

    @staticmethod
    def get_filter_options() -> Dict[str, Dict[str, str]]:
        """
        获取过滤器的选项定义

        Returns:
            过滤器选项字典
        """
        return {
            "modality": {
                "": "所有类型",
                "image": "图片",
                "table": "表格",
                "text": "文本",
                "document": "文档",
                "audio": "音频",
            },
            "role": {
                "": "所有角色",
                "scene_issue": "现场问题",
                "meter": "表具",
                "runtime_table": "运行表",
            },
            "time": {
                "all": "所有时间",
                "7d": "最近7天",
                "30d": "最近30天",
            },
        }


class AssetTableRowClickHandler:
    """
    资产表格行点击处理器

    处理表格行点击事件，支持不同的数据格式
    """

    @staticmethod
    def extract_row_id(e: Any) -> Optional[str]:
        """从行点击事件中提取资产 ID。

        兼容多种 NiceGUI/QTable rowClick 事件形态，例如：
        - e.args == row
        - e.args == [row]
        - e.args == [mouse_event, row, row_index]
        - e.args == {"row": row, ...}
        """
        args = e.args
        print(f"[DEBUG] asset_table rowClick raw args: {args!r}")

        # 统一成候选列表，方便遍历查找真正的行对象
        candidates: List[Any]
        if isinstance(args, list):
            if not args:
                print("[DEBUG] asset_table rowClick: empty list args")
                return None
            candidates = list(args)
        else:
            candidates = [args]

        row_obj: Optional[Dict[str, Any]] = None
        asset_id: Optional[str] = None

        for item in candidates:
            # 直接就是行字典
            if isinstance(item, dict) and "id" in item:
                row_obj = item
                asset_id = item.get("id")
                break

            # 包裹在 {"row": {...}} 里的行字典
            if isinstance(item, dict) and "row" in item:
                inner = item.get("row")
                if isinstance(inner, dict) and "id" in inner:
                    row_obj = inner
                    asset_id = inner.get("id")
                    break

        if not row_obj or not asset_id:
            print(f"[DEBUG] asset_table rowClick: no usable row with 'id' found in args {args!r}")
            return None

        print(f"[DEBUG] asset_table rowClick resolved asset_id={asset_id}")
        return str(asset_id)


# ==================== 便捷函数 ====================

def get_asset_table_columns() -> List[Dict[str, Any]]:
    """
    获取资产表格列定义（便捷函数）

    Returns:
        列定义列表
    """
    return AssetTableHelper.get_table_columns()


def apply_asset_filters(
    assets: List[Dict[str, Any]],
    modality_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    time_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    应用过滤条件到资产列表（便捷函数）

    Args:
        assets: 资产列表
        modality_filter: 模态类型过滤
        role_filter: 角色过滤
        time_filter: 时间过滤

    Returns:
        过滤后的资产列表
    """
    return AssetTableHelper.apply_filters(assets, modality_filter, role_filter, time_filter)


def extract_asset_id_from_row_click(e: Any) -> Optional[str]:
    """
    从行点击事件中提取资产 ID（便捷函数）

    Args:
        e: 行点击事件参数

    Returns:
        资产 ID
    """
    return AssetTableRowClickHandler.extract_row_id(e)
