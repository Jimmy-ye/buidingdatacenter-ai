"""
UI 组件模块

本模块包含从 main_page() 拆分的可复用 UI 组件

版本: v1.0
创建时间: 2025-01-22
"""

from desktop.nicegui_app.ui.dialogs import (
    ProjectDialog,
    show_create_project_dialog,
    show_edit_project_dialog,
)

__all__ = [
    "ProjectDialog",
    "show_create_project_dialog",
    "show_edit_project_dialog",
]
