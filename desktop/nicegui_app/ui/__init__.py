"""
UI 组件模块

本模块包含从 main_page() 拆分的可复用 UI 组件

版本: v1.0
创建时间: 2025-01-22
"""

from desktop.nicegui_app.ui.dialogs import (
    ProjectDialog,
    EngineeringNodeDialog,
    AssetDialog,
    show_create_project_dialog,
    show_edit_project_dialog,
    show_create_building_dialog,
    show_edit_building_dialog,
    show_delete_building_dialog,
    show_upload_asset_dialog,
    show_delete_asset_dialog,
)

__all__ = [
    "ProjectDialog",
    "EngineeringNodeDialog",
    "AssetDialog",
    "show_create_project_dialog",
    "show_edit_project_dialog",
    "show_create_building_dialog",
    "show_edit_building_dialog",
    "show_delete_building_dialog",
    "show_upload_asset_dialog",
    "show_delete_asset_dialog",
]
