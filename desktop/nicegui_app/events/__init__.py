"""
事件处理模块

本模块包含从 main_page() 中提取的事件处理逻辑。

版本: v1.0
创建时间: 2026-01-23
"""

from desktop.nicegui_app.events.asset_events import (
    AssetStateRef,
    AssetUIContext,
    on_asset_row_click,
    on_run_ocr_click,
    on_run_scene_llm_click,
    on_upload_asset_click,
    on_delete_asset_click,
)

__all__ = [
    "AssetStateRef",
    "AssetUIContext",
    "on_asset_row_click",
    "on_run_ocr_click",
    "on_run_scene_llm_click",
    "on_upload_asset_click",
    "on_delete_asset_click",
]
