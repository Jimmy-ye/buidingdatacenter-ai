"""
资产相关事件处理

本模块包含资产表格、详情、OCR/LLM 等相关的事件处理逻辑。

版本: v1.0
创建时间: 2026-01-23
"""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from nicegui import ui
from desktop.nicegui_app.ui.dialogs import (
    show_upload_asset_dialog,
    show_delete_asset_dialog,
)


@dataclass
class AssetStateRef:
    """
    资产状态引用（容器）

    使用容器而不是直接值，确保事件处理函数中的修改对外部可见。
    """
    selected_asset: Optional[Dict[str, Any]] = None
    all_assets_for_device: Optional[List[Dict[str, Any]]] = None

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


async def on_run_ocr_click(
    ctx: AssetUIContext,
    backend_base_url: str,
    get_asset_detail_func: Callable[[str], Awaitable[Dict[str, Any]]],
    enrich_asset_func: Callable[[Dict[str, Any]], None],
    update_detail_func: Callable[[], None],
) -> None:
    """运行 OCR 的点击事件处理。

    该函数基于当前选中的资产，调用后端 /assets/{asset_id}/parse_image 接口，
    并在完成后刷新资产详情和右侧详情面板。
    """

    selected_asset = ctx.asset_state.selected_asset
    if not selected_asset:
        ui.notify("请先在列表中选择一个资产", color="warning")
        return

    modality = str(selected_asset.get("modality") or "").lower()
    if modality != "image":
        ui.notify("当前资产不是图片，无法运行 OCR", color="warning")
        return

    asset_id = selected_asset.get("id")
    if not asset_id:
        ui.notify("资产ID缺失，无法运行 OCR", color="negative")
        return

    ctx.inference_status_label.text = "OCR 处理中……"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{backend_base_url}/assets/{asset_id}/parse_image")
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        ctx.inference_status_label.text = "OCR 失败"
        ui.notify(f"运行 OCR 失败: {exc}", color="negative")
        return

    try:
        detail = await get_asset_detail_func(str(asset_id))
        enrich_asset_func(detail)
        ctx.asset_state.selected_asset = detail
    except Exception as exc:  # noqa: BLE001
        ui.notify(f"刷新资产详情失败: {exc}", color="negative")

    update_detail_func()


async def on_upload_asset_click(
    ctx: AssetUIContext,
    project_id: str,
    device_id: str,
    project_name: str,
    backend_base_url: str,
    enrich_asset_func: Callable[[Dict[str, Any]], None],
    apply_asset_filters_func: Callable[[], None],
) -> None:
    """上传资产点击事件处理。

    该函数负责调用上传资产对话框并在上传成功后更新资产列表和过滤结果。
    """

    async def on_upload_success(new_asset: Dict[str, Any]) -> None:
        """上传成功后的回调。"""
        enrich_asset_func(new_asset)
        if ctx.asset_state.all_assets_for_device is None:
            ctx.asset_state.all_assets_for_device = []
        ctx.asset_state.all_assets_for_device.append(new_asset)
        apply_asset_filters_func()

    show_upload_asset_dialog(
        project_id=project_id,
        device_id=device_id,
        project_name=project_name,
        backend_base_url=backend_base_url,
        on_success=on_upload_success,
    )


async def on_delete_asset_click(
    ctx: AssetUIContext,
    backend_base_url: str,
    apply_asset_filters_func: Callable[[], None],
) -> None:
    """删除资产点击事件处理。

    该函数基于当前选中的资产，调用删除资产对话框，并在删除成功后
    更新资产列表和右侧详情状态。
    """

    selected_asset = ctx.asset_state.selected_asset
    if not selected_asset:
        ui.notify("请先在列表中选择一个资产", color="warning")
        return

    asset_id = selected_asset.get("id") if selected_asset else None
    if not asset_id:
        ui.notify("资产ID缺失，无法删除", color="negative")
        return

    async def on_delete_success(deleted_asset_id: str) -> None:
        """删除成功后的回调。"""
        all_assets = ctx.asset_state.all_assets_for_device or []
        remaining: List[Dict[str, Any]] = [
            a for a in all_assets if str(a.get("id")) != str(deleted_asset_id)
        ]
        ctx.asset_state.all_assets_for_device = remaining
        ctx.asset_state.selected_asset = None
        apply_asset_filters_func()

    show_delete_asset_dialog(
        asset_id=asset_id,
        backend_base_url=backend_base_url,
        on_success=on_delete_success,
    )


async def on_run_scene_llm_click(
    ctx: AssetUIContext,
    backend_base_url: str,
    get_asset_detail_func: Callable[[str], Awaitable[Dict[str, Any]]],
    enrich_asset_func: Callable[[Dict[str, Any]], None],
    update_detail_func: Callable[[], None],
) -> None:
    """运行现场问题 LLM 的点击事件处理。

    该函数基于当前选中的资产，调用后端 /assets/{asset_id}/route_image 接口，
    将图片资产提交到 LLM 管线，并在完成后刷新资产详情和右侧详情面板。
    """

    selected_asset = ctx.asset_state.selected_asset
    if not selected_asset:
        ui.notify("请先在列表中选择一个资产", color="warning")
        return

    modality = str(selected_asset.get("modality") or "").lower()
    role = str(selected_asset.get("content_role") or "").lower()
    if modality != "image":
        ui.notify("当前资产不是图片，无法提交 LLM 分析", color="warning")
        return
    if role not in {"scene_issue", "meter"}:
        ui.notify(
            "建议对角色为 scene_issue 或 meter 的图片运行现场问题分析",
            color="warning",
        )

    asset_id = selected_asset.get("id")
    if not asset_id:
        ui.notify("资产ID缺失，无法提交 LLM 分析", color="negative")
        return

    ctx.inference_status_label.text = "已提交到 LLM 管线，等待分析结果……"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{backend_base_url}/assets/{asset_id}/route_image")
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        ui.notify(f"提交 LLM 分析失败: {exc}", color="negative")
        return

    try:
        detail = await get_asset_detail_func(str(asset_id))
        enrich_asset_func(detail)
        ctx.asset_state.selected_asset = detail
    except Exception as exc:  # noqa: BLE001
        ui.notify(f"刷新资产详情失败: {exc}", color="negative")

    update_detail_func()
