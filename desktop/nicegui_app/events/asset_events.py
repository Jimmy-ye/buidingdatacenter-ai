"""
资产相关事件处理

本模块包含资产表格、详情、OCR/LLM 等相关的事件处理逻辑。

版本: v1.0
创建时间: 2026-01-23
"""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

import nicegui as ui


@dataclass
class AssetStateRef:
    """
    资产状态引用（容器）

    使用容器而不是直接值，确保事件处理函数中的修改对外部可见。
    """
    selected_asset: Optional[Dict[str, Any]] = None
    all_assets_for_device: list[Dict[str, Any]] = None

    def __post_init__(self):
        if self.all_assets_for_device is None:
            self.all_assets_for_device = []


@dataclass
class AssetUIContext:
    """
    资产 UI 上下文

    包含资产相关事件处理需要的 UI 元素和状态引用。
    """
    # 状态引用
    asset_state: AssetStateRef

    # UI 元素 - 资产表格
    asset_table: Any

    # UI 元素 - 详情面板
    detail_title: Any
    detail_meta: Any
    detail_body: Any
    detail_tags: Any

    # UI 元素 - 图片预览
    preview_image: Any
    preview_button: Any

    # UI 元素 - OCR/LLM 相关
    ocr_objects_label: Any
    ocr_text_label: Any
    llm_summary_label: Any
    inference_status_label: Any
    run_ocr_button: Any
    run_llm_button: Any


async def on_asset_row_click(
    ctx: AssetUIContext,
    e: Any,
    get_asset_detail_func: Callable[[str], Awaitable[Dict[str, Any]]],
    enrich_asset_func: Callable[[Dict[str, Any]], None],
    update_detail_func: Callable[[], None],
    on_preview_func: Optional[Callable[[], Awaitable[None]]] = None,
) -> None:
    """
    处理资产表格行点击事件

    Args:
        ctx: 资产 UI 上下文
        e: NiceGUI 行点击事件参数
        get_asset_detail_func: 获取资产详情的异步函数
        enrich_asset_func: 丰富资产数据的函数
        update_detail_func: 更新详情面板的函数
        on_preview_func: 图片预览函数（可选）
    """
    from desktop.nicegui_app.ui.tables import extract_asset_id_from_row_click

    # 使用组件化的行点击处理逻辑
    asset_id = extract_asset_id_from_row_click(e)
    if asset_id is None:
        return

    try:
        # 调用后端 API 获取完整资产详情
        detail = await get_asset_detail_func(str(asset_id))
        enrich_asset_func(detail)

        # 更新状态引用
        ctx.asset_state.selected_asset = detail
    except Exception:
        ui.notify("加载资产详情失败，请稍后重试", color="negative")
        # 降级：使用事件参数中的数据
        ctx.asset_state.selected_asset = (
            e.args if isinstance(e.args, dict)
            else (e.args[0] if isinstance(e.args, list) and e.args else {})
        )

    # 更新详情面板
    update_detail_func()

    # 如果是图片资产，自动触发一次预览
    if on_preview_func is not None:
        try:
            modality = (ctx.asset_state.selected_asset or {}).get("modality")
            if modality == "image":
                await on_preview_func()
        except Exception:
            # 预览失败不影响基本详情展示
            pass
