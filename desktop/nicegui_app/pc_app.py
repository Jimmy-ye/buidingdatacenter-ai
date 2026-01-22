from __future__ import annotations

import base64
import os
import subprocess
import sys
import inspect
from datetime import datetime, timedelta
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from nicegui import app, ui, events
from nicegui.events import ValueChangeEventArguments

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.config.settings import get_settings

BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1"
SETTINGS = get_settings()
ASSET_WEB_PREFIX = "/local_assets"
BASE_ASSET_DIR = os.path.abspath(SETTINGS.local_storage_dir)
app.add_static_files(ASSET_WEB_PREFIX, BASE_ASSET_DIR)

# 简单的前端版本号标记，便于确认是否加载了最新的 PC UI 代码
UI_VERSION = "PC UI v0.3.6-refactor-stage3"

# ==================== 新增：API 客户端（重构阶段 1）====================
# 创建统一的 API 客户端实例
# 旧的 API 函数保留以确保向后兼容，但建议逐步迁移到 BackendClient
try:
    from desktop.nicegui_app.api.client import BackendClient
    backend_client = BackendClient()
except ImportError:
    # 如果导入失败，创建一个空对象（向后兼容）
    backend_client = None
    logger = None
# ======================================================================

# ==================== 新增：状态管理（重构阶段 2）====================
# 使用集中式状态管理替代闭包变量
# 新旧状态可以共存，逐步迁移
try:
    from desktop.nicegui_app.state.store import app_state, get_current_project
    STATE_MANAGEMENT_ENABLED = True
except ImportError:
    # 如果导入失败，禁用状态管理
    app_state = None
    STATE_MANAGEMENT_ENABLED = False
    def get_current_project():
        return None
# ======================================================================

# ==================== 新增：UI 组件（重构阶段 3）====================
# 可复用的 UI 组件
# 逐步从 main_page() 拆分出来的对话框、面板等组件
try:
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
    UI_COMPONENTS_ENABLED = True
except ImportError:
    # 如果导入失败，禁用 UI 组件
    UI_COMPONENTS_ENABLED = False
    ProjectDialog = None
    EngineeringNodeDialog = None
    AssetDialog = None
    show_create_project_dialog = None
    show_edit_project_dialog = None
    show_create_building_dialog = None
    show_edit_building_dialog = None
    show_delete_building_dialog = None
    show_upload_asset_dialog = None
    show_delete_asset_dialog = None
# ======================================================================


async def fetch_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BACKEND_BASE_URL}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


async def list_projects() -> List[Dict[str, Any]]:
    # 简化：直接调用项目列表，如果没有该接口，可后续调整
    try:
        return await fetch_json("/projects/")
    except Exception:
        return []


async def get_structure_tree(project_id: str) -> Dict[str, Any]:
    return await fetch_json(f"/projects/{project_id}/structure_tree")


async def list_assets_for_device(device_id: str) -> List[Dict[str, Any]]:
    """List assets for a device via the backend /assets endpoint with device_id filter."""
    return await fetch_json("/assets/", params={"device_id": device_id})


async def get_asset_detail(asset_id: str) -> Dict[str, Any]:
    return await fetch_json(f"/assets/{asset_id}")


def extract_keywords(asset: Dict[str, Any]) -> str:
    """从资产中提取有意义的关键词用于表格展示"""
    keywords: List[str] = []

    # 1. 从 structured_payloads 数组中提取（优先级最高）
    payloads = asset.get("structured_payloads") or []
    for sp in payloads:
        schema = sp.get("schema_type", "")
        payload = sp.get("payload", {})

        # 图片类型：提取 global_tags 和 OCR 检测到的对象
        if schema == "image_annotation":
            # global_tags
            global_tags = payload.get("global_tags") or []
            for tag in global_tags[:2]:
                if isinstance(tag, str) and len(tag) > 0:
                    keywords.append(tag)

            # OCR 对象标签（top 2）
            annotations = payload.get("annotations", {})
            objects = annotations.get("objects", [])
            for obj in objects[:2]:
                label = obj.get("label", "")
                if isinstance(label, str) and len(label) > 0 and len(label) < 20:
                    keywords.append(label)

        # 现场问题类型
        elif schema == "scene_issue_report_v1":
            issue_category = payload.get("issue_category", "")
            if issue_category:
                keywords.append(issue_category)
            severity = payload.get("severity", "")
            if severity:
                keywords.append(f"严重度:{severity}")

        # 表格类型：提取数据质量
        elif schema == "table_data":
            quality = payload.get("data_quality", "")
            if quality:
                keywords.append(f"质量:{quality}")

    # 2. 如果还没有足够关键词，从 content_role 提取
    if len(keywords) < 2:
        role = asset.get("content_role")
        if role:
            # 将 role 翻译成中文
            role_map = {
                "meter": "仪表",
                "scene_issue": "现场问题",
                "nameplate": "铭牌",
                "energy_table": "能耗表",
                "runtime_table": "运行表",
            }
            role_cn = role_map.get(role, role)
            keywords.append(role_cn)

    # 3. 从 tags 提取（排除 environment 和 source）
    tags = asset.get("tags") or {}
    if isinstance(tags, dict):
        for key, value in tags.items():
            if key in {"environment", "source"}:
                continue
            if value not in (None, ""):
                keywords.append(str(value))

    # 4. 从 status 提取（parsed 状态）
    status = asset.get("status", "")
    if status:
        status_map = {
            "parsed_ocr_ok": "OCR完成",
            "parsed_scene_llm": "场景分析完成",
            "pending": "待处理",
        }
        status_cn = status_map.get(status, status)
        keywords.append(status_cn)

    # 去重并限制数量
    seen: set[str] = set()
    dedup: List[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            dedup.append(kw)

    return ", ".join(dedup[:3])


def enrich_asset(asset: Dict[str, Any]) -> None:
    capture_time = asset.get("capture_time")
    short_date = "-"
    if capture_time:
        try:
            ct_str = str(capture_time)
            if ct_str.endswith("Z"):
                ct_str = ct_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ct_str)
            short_date = dt.strftime("%m-%d")
        except Exception:
            short_date = "-"
    asset["short_date"] = short_date

    try:
        asset["keywords"] = extract_keywords(asset)
    except Exception:
        asset["keywords"] = ""


def build_tree_nodes(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将后端返回的 structure_tree 转成 NiceGUI tree 所需格式."""

    def convert(node: Dict[str, Any]) -> Dict[str, Any]:
        raw_id = node.get("id") or node.get("node_id")
        label = node.get("name") or node.get("type") or "node"
        node_type = node.get("type")
        icon = "devices_other" if node_type == "device" else "folder"

        # 为了在 on_select 回调中简单区分类型，这里将 type 编码进 id 字符串
        tree_id = f"{node_type}:{raw_id}" if node_type and raw_id else str(raw_id or "")

        children = [convert(child) for child in node.get("children", [])]
        return {
            "id": tree_id,
            "label": label,
            "icon": icon,
            "children": children,
        }

    root = tree.get("tree") or tree
    if isinstance(root, dict):
        return [convert(root)]
    return []


def main_page() -> None:
    """构建页面骨架，数据通过异步任务后续填充，避免页面加载超时。"""

    loading_label = ui.label("正在加载项目，请稍候...").classes("text-caption text-grey")
    status_spinner = ui.spinner().props("size=18 color=primary").classes("q-ml-sm")
    status_spinner.visible = True

    with ui.row().style("height: 100vh; width: 100vw;"):
        # 左侧：工程结构树（缩小到 280px）
        with ui.card().style("width: 280px; height: 100%; overflow: auto;"):
            ui.label("工程结构").classes("text-h6")

            with ui.row().classes("items-center q-mt-sm q-gutter-xs"):
                project_select = ui.select({}, value=None, label="项目").props("dense outlined")
                project_create_btn = ui.button("＋项目").props("dense outlined")
                project_edit_btn = ui.button("编辑").props("dense outlined")
                project_delete_btn = ui.button("删除").props("dense outlined")

            tree_search = ui.input(placeholder="搜索结构名称...").props("dense clearable").classes("q-mt-sm")

            with ui.row().classes("items-center q-mt-sm q-gutter-xs"):
                building_add_btn = ui.button("＋楼栋").props("dense outlined")
                node_edit_btn = ui.button("编辑节点").props("dense outlined")
                node_delete_btn = ui.button("删除节点").props("dense outlined")

            tree_widget = ui.tree([]).props("node-key=id")

        # 右侧：顶部项目信息 + 资产列表 / 详情两列布局
        with ui.column().style("flex-grow: 1; height: 100%; overflow: auto;"):
            with ui.column().classes("q-pa-md"):
                with ui.row().classes("items-center justify-between w-full"):
                    project_title = ui.label("未选择项目").classes("text-h6")
                    with ui.row().classes("items-center q-gutter-sm"):
                        ui.label(UI_VERSION).classes("text-caption text-grey")
                        refresh_button = ui.button(icon="refresh").props("flat round dense")
                project_meta = ui.label("").classes("text-caption text-grey")

                ui.separator()

                with ui.row().classes("w-full q-mt-md items-start no-wrap"):
                    # 左列：资产过滤器 + 列表（固定 40% 宽度，防止内容撑开）
                    with ui.column().style("flex: 0 0 40%; width: 40%; min-width: 320px; overflow: hidden;"):
                        ui.label("资产列表").classes("text-subtitle1")

                        with ui.row().classes("items-center q-mt-sm q-gutter-sm"):
                            modality_filter = ui.select(
                                {
                                    "": "全部类型",
                                    "image": "图片",
                                    "table": "表格",
                                    "document": "文档",
                                },
                                value="",
                                label="类型",
                            ).props("dense outlined")
                            role_filter = ui.select(
                                {
                                    "": "全部角色",
                                    "meter": "仪表",
                                    "scene_issue": "现场问题",
                                    "nameplate": "铭牌",
                                    "energy_table": "能耗表",
                                    "runtime_table": "运行表",
                                },
                                value="",
                                label="角色",
                            ).props("dense outlined")
                            time_filter = ui.select(
                                {
                                    "all": "所有时间",
                                    "7d": "最近7天",
                                    "30d": "最近30天",
                                },
                                value="all",
                                label="时间",
                            ).props("dense outlined")

                        result_count_label = ui.label("").classes("text-caption text-grey q-mt-xs")

                        asset_table = ui.table(
                            columns=[
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
                            ],
                            rows=[],
                        ).props('row-key="id" dense flat').classes("w-full")

                        with ui.row().classes("q-mt-sm q-gutter-sm"):
                            upload_asset_button = ui.button("上传图片资产")
                            delete_asset_button = ui.button("删除选中资产", color="negative")

                    # 右列：资产详情 + 图片预览 + OCR/LLM 结果（固定 60% 宽度，防止内容撑开）
                    with ui.column().style("flex: 0 0 60%; width: 60%; min-width: 0; overflow: hidden;"):
                        with ui.card().classes("w-full"):
                            ui.label("基本信息").classes("text-subtitle2 q-mb-sm")
                            detail_title = ui.label("资产详情").classes("text-subtitle1")
                            detail_meta = ui.label("").classes("text-caption text-grey q-mb-xs")
                            detail_body = ui.label("请选择左侧设备，加载资产后查看详情。").classes("text-body2").style("word-break: break-word;")
                            detail_tags = ui.label("").classes("text-caption text-grey")

                        with ui.card().classes("w-full q-mt-sm"):
                            ui.label("图片预览").classes("text-subtitle2 q-mb-sm")
                            with ui.row().classes("items-center justify-center").style("width: 100%; min-width: 0;"):
                                preview_image = ui.image().props("loading=eager fit=contain").style(
                                    "width: 100%; max-width: 550px; height: 350px; min-width: 200px; background: #f5f5f5; border-radius: 4px;"
                                )
                                preview_image.visible = False
                            with ui.row().classes("q-mt-sm q-gutter-sm"):
                                preview_button = ui.button("预览图片")
                                open_file_button = ui.button("打开原始文件")

                            # 大图预览对话框
                            preview_dialog = ui.dialog()
                            with preview_dialog, ui.card():
                                dialog_image = ui.image().props("loading=eager").style(
                                    "max-width: 80vw; max-height: 80vh; object-fit: contain;"
                                )

                        with ui.card().classes("w-full q-mt-sm").style("overflow: auto; max-height: 500px;"):
                            ui.label("OCR/LLM 识别结果").classes("text-subtitle2 q-mb-sm")
                            inference_status_label = ui.label("").classes("text-caption text-grey q-mb-xs")
                            with ui.row().classes("q-mb-sm q-gutter-sm"):
                                run_ocr_button = ui.button("运行 OCR")
                                run_llm_button = ui.button("生成现场问题报告")
                            ocr_objects_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;")
                            ocr_text_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;")
                            llm_summary_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;")

    # ==================== 旧状态变量（向后兼容）====================
    projects_cache: List[Dict[str, Any]] = []
    full_tree_nodes: List[Dict[str, Any]] = []
    selected_asset: Optional[Dict[str, Any]] = None
    all_assets_for_device: List[Dict[str, Any]] = []
    current_device_id: Optional[str] = None
    current_tree_node_type: Optional[str] = None
    current_tree_node_id: Optional[str] = None
    # ======================================================================

    # ==================== 新增：状态同步适配层（重构阶段 2）====================
    if STATE_MANAGEMENT_ENABLED and app_state:
        def sync_state_to_old_vars():
            """
            将新状态同步到旧变量（兼容层）

            确保使用旧变量的代码仍然可以正常工作
            """
            nonlocal projects_cache, full_tree_nodes, selected_asset
            nonlocal all_assets_for_device, current_device_id
            nonlocal current_tree_node_type, current_tree_node_id

            # 同步项目状态
            projects_cache = app_state.project.projects

            # 同步树状态
            full_tree_nodes = app_state.tree.all_nodes
            current_tree_node_type = app_state.tree.selected_node_type
            current_tree_node_id = app_state.tree.selected_node_id

            # 同步资产状态
            all_assets_for_device = app_state.asset.all_assets
            selected_asset = app_state.asset.selected_asset
            current_device_id = app_state.asset.current_device_id

        def sync_old_vars_to_state():
            """
            将旧变量同步到新状态（兼容层）

            当旧变量被修改时，同步更新新状态
            """
            if not app_state:
                return

            # 同步项目状态
            app_state.project.set_projects(projects_cache)
            if project_select.value:
                app_state.project.set_current_project(project_select.value)

            # 同步树状态
            app_state.tree.set_nodes(full_tree_nodes)
            app_state.tree.set_selected_node(current_tree_node_type, current_tree_node_id)

            # 同步资产状态
            app_state.asset.set_assets(all_assets_for_device)
            app_state.asset.set_selected_asset(selected_asset)
            app_state.asset.current_device_id = current_device_id

        # 初始化时同步一次
        sync_state_to_old_vars()
    else:
        # 如果状态管理未启用，创建空函数
        def sync_state_to_old_vars():
            pass

        def sync_old_vars_to_state():
            pass
    # ======================================================================

    def update_inference_status() -> None:
        nonlocal selected_asset
        if not selected_asset:
            inference_status_label.text = ""
            run_ocr_button.disabled = True
            run_llm_button.disabled = True
            return

        status = str(selected_asset.get("status") or "").lower()
        modality = str(selected_asset.get("modality") or "").lower()
        role = str(selected_asset.get("content_role") or "").lower()

        msg = ""
        if not status:
            msg = "未解析，点击下方按钮运行 OCR 或提交 LLM 分析"
        elif status == "parsed_ocr_ok":
            msg = "OCR 完成（置信度较高）"
        elif status == "parsed_ocr_low_conf":
            msg = "OCR 完成（置信度较低，建议人工复核）"
        elif status == "pending_scene_llm":
            msg = "已提交到 LLM 管线，等待分析结果……"
        elif status == "parsed_scene_llm":
            msg = "LLM 场景分析已完成"
        else:
            msg = f"当前状态: {status}"

        inference_status_label.text = msg

        is_image = modality == "image"
        run_ocr_button.disabled = not is_image
        run_llm_button.disabled = not (is_image and role in {"scene_issue", "meter"})

    def get_current_project() -> Optional[Dict[str, Any]]:
        if not project_select.value:
            return None
        for p in projects_cache:
            if str(p.get("id")) == str(project_select.value):
                return p
        return None

    def update_project_header() -> None:
        project = get_current_project()
        if not project:
            project_title.text = "未选择项目"
            project_meta.text = ""
            return
        name = project.get("name") or "未命名项目"
        status = project.get("status") or ""
        client = project.get("client") or ""
        location = project.get("location") or ""
        tags = project.get("tags") or {}
        env = tags.get("environment")

        title = name
        if env == "test":
            title = f"{name} [TEST]"
        project_title.text = title

        parts: List[str] = []
        if client:
            parts.append(str(client))
        if location:
            parts.append(str(location))
        if status:
            parts.append(f"状态: {status}")
        project_meta.text = " • ".join(parts)

    async def reload_projects_and_tree(selected_project_id: Optional[str] = None) -> None:
        nonlocal projects_cache, selected_asset
        status_spinner.visible = True

        try:
            projects = await list_projects()
        except Exception:
            projects = []

        if not projects:
            projects_cache = []
            project_select.options = {}
            project_select.value = None
            tree_widget._props["nodes"] = []
            tree_widget.update()
            loading_label.text = "暂无项目，请先在后端创建项目"
            status_spinner.visible = False
            selected_asset = None
            update_asset_detail()
            return

        projects_cache = projects
        options = {p["id"]: p["name"] for p in projects}
        project_select.options = options

        target_id = None
        if selected_project_id is not None:
            for p in projects:
                if str(p["id"]) == str(selected_project_id):
                    target_id = p["id"]
                    break
        if target_id is None:
            target_id = projects[0]["id"]

        project_select.value = target_id
        loading_label.text = ""
        status_spinner.visible = False
        update_project_header()
        await reload_tree()

    def update_asset_detail() -> None:
        nonlocal selected_asset
        if not selected_asset:
            detail_title.text = "资产详情"
            detail_meta.text = ""
            detail_body.text = "请选择左侧设备，加载资产后查看详情。"
            detail_tags.text = ""
            preview_image.visible = False
            preview_image.source = ""
            preview_button.disabled = True
            inference_status_label.text = ""
            run_ocr_button.disabled = True
            run_llm_button.disabled = True
            ocr_objects_label.text = ""
            ocr_text_label.text = ""
            llm_summary_label.text = ""
            return
        asset = selected_asset
        title = asset.get("title") or asset.get("id") or "资产详情"
        modality = asset.get("modality") or "-"
        role = asset.get("content_role") or "-"
        capture_time = asset.get("capture_time") or "-"
        description = asset.get("description") or "(无描述)"
        tags = asset.get("tags") or {}

        detail_title.text = str(title)
        detail_meta.text = f"类型: {modality} • 角色: {role} • 采集时间: {capture_time}"
        detail_body.text = str(description)
        detail_tags.text = f"Tags: {tags}" if tags else ""
        # 不再自动隐藏预览图，让用户可以连续预览
        if str(modality).lower() == "image":
            preview_button.disabled = False
        else:
            preview_button.disabled = True

        # 填充 OCR/LLM 识别结果区域
        ocr_objects_label.text = ""
        ocr_text_label.text = ""
        llm_summary_label.text = ""

        update_inference_status()

        # 对于表具类型，只显示 LLM 结果，不显示 OCR 详细内容
        is_meter = (str(asset.get("content_role", "")) == "meter")

        # 从 structured_payloads 数组中提取数据
        payloads = asset.get("structured_payloads") or []
        for sp in payloads:
            schema = sp.get("schema_type", "")
            data = sp.get("payload", {})

            # 图片 OCR 识别结果（表具类型跳过）
            if schema == "image_annotation" and not is_meter:
                annotations = data.get("annotations", {}) or {}
                ocr_lines = annotations.get("ocr_lines") or []

                # 显示所有 OCR 文本（不限制行数）
                if ocr_lines:
                    texts = [line.get("text", "") for line in ocr_lines if line.get("text")]
                    if texts:
                        ocr_text = "\n".join(texts)
                        ocr_text_label.text = ocr_text
                else:
                    # 回退到 derived_text 字段
                    derived_text = data.get("derived_text")
                    if isinstance(derived_text, str) and derived_text:
                        ocr_text_label.text = derived_text

                # 显示 OCR 统计信息
                stats = data.get("stats", {})
                if stats:
                    engine = stats.get("engine", "unknown")
                    avg_conf = stats.get("avg_confidence", 0)
                    if isinstance(avg_conf, (int, float)):
                        ocr_objects_label.text = f"OCR 引擎: {engine}\n平均置信度: {avg_conf:.1%}\n识别行数: {len(ocr_lines)}"

                # 提取并显示所有数字（用于调试）
                if ocr_lines:
                    import re
                    all_numbers = []
                    for line in ocr_lines:
                        text = line.get("text", "")
                        conf = line.get("confidence", 0)
                        # 提取所有数字（包括小数）
                        numbers = re.findall(r"\d+\.?\d*", text)
                        for num in numbers:
                            try:
                                val = float(num)
                                all_numbers.append({
                                    "value": val,
                                    "text": text,
                                    "confidence": conf
                                })
                            except ValueError:
                                pass

                    if all_numbers:
                        # 按数值排序
                        all_numbers.sort(key=lambda x: x["value"])

                        # 显示所有提取的数字
                        debug_lines = []
                        for item in all_numbers:
                            val = item["value"]
                            txt = item["text"]
                            conf = item.get("confidence", 0)
                            debug_lines.append(f"  {val:6.2f} (置信度: {conf:.1%}) - 来自: \"{txt}\"")

                        # 添加到 OCR 统计信息下方
                        current_text = ocr_objects_label.text or ""
                        ocr_objects_label.text = f"{current_text}\n\n【提取到的所有数字】\n" + "\n".join(debug_lines)

            # 现场问题 LLM 分析结果
            elif schema == "scene_issue_report_v1":
                # 显示问题标题
                issue_title = data.get("title", "")
                if issue_title:
                    llm_summary_label.text = f"【问题】{issue_title}\n"

                # 显示问题摘要
                summary = data.get("summary", "")
                if summary:
                    current_text = llm_summary_label.text or ""
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    llm_summary_label.text = current_text + f"\n【摘要】{summary}"

                # 显示推荐措施
                actions = data.get("recommended_actions") or []
                if actions:
                    current_text = llm_summary_label.text or ""
                    action_text = "\n".join([f"• {a}" for a in actions[:3]])
                    llm_summary_label.text = current_text + f"\n【建议】\n{action_text}"

    def apply_tree_filter() -> None:
        """根据搜索框过滤工程结构树。"""
        text = (tree_search.value or "").strip().lower()
        if not full_tree_nodes:
            tree_widget._props["nodes"] = []
            tree_widget.update()
            return
        if not text:
            tree_widget._props["nodes"] = full_tree_nodes
            tree_widget.update()
            return

        def filter_node(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            label = str(node.get("label") or "").lower()
            children = node.get("children") or []
            filtered_children: List[Dict[str, Any]] = []
            for child in children:
                filtered = filter_node(child)
                if filtered is not None:
                    filtered_children.append(filtered)
            if text in label or filtered_children:
                new_node = dict(node)
                new_node["children"] = filtered_children
                return new_node
            return None

        filtered_roots: List[Dict[str, Any]] = []
        for root in full_tree_nodes:
            filtered = filter_node(root)
            if filtered is not None:
                filtered_roots.append(filtered)
        tree_widget._props["nodes"] = filtered_roots
        tree_widget.update()

    def apply_asset_filters() -> None:
        nonlocal selected_asset
        if not all_assets_for_device:
            asset_table.rows = []
            asset_table.update()
            selected_asset = None
            update_asset_detail()
            result_count_label.text = "共 0 条"
            return

        modality_value = modality_filter.value or ""
        role_value = (role_filter.value or "").strip().lower()
        time_value = time_filter.value or "all"

        now = datetime.utcnow()
        cutoff: Optional[datetime] = None
        if time_value == "7d":
            cutoff = now - timedelta(days=7)
        elif time_value == "30d":
            cutoff = now - timedelta(days=30)

        filtered: List[Dict[str, Any]] = []
        for asset in all_assets_for_device:
            if modality_value and asset.get("modality") != modality_value:
                continue
            role = (asset.get("content_role") or "").lower()
            if role_value and role != role_value:
                continue
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

        asset_table.rows = filtered
        asset_table.update()
        result_count_label.text = f"共 {len(filtered)} 条"

        selected_asset = None
        update_asset_detail()

    async def on_refresh_click() -> None:
        nonlocal selected_asset
        loading_label.text = "正在刷新工程结构..."
        status_spinner.visible = True
        asset_table.rows = []
        asset_table.update()
        selected_asset = None
        update_asset_detail()
        await reload_tree()

    async def reload_tree() -> None:
        nonlocal selected_asset, current_device_id, current_tree_node_type, current_tree_node_id
        # 切换项目或刷新结构树时，重置资产相关状态
        current_device_id = None
        current_tree_node_type = None
        current_tree_node_id = None
        all_assets_for_device.clear()
        asset_table.rows = []
        asset_table.update()
        selected_asset = None
        update_asset_detail()
        modality_filter.value = ""
        role_filter.value = ""
        time_filter.value = "all"
        update_project_header()
        if not project_select.value:
            tree_widget._props["nodes"] = []
            tree_widget.update()
            status_spinner.visible = False
            return
        try:
            data = await get_structure_tree(str(project_select.value))
            nodes = build_tree_nodes(data)
            full_tree_nodes.clear()
            full_tree_nodes.extend(nodes)
            apply_tree_filter()
            loading_label.text = ""
            status_spinner.visible = False
        except Exception:
            # 后端不可用或结构树接口异常时，仅在页面上给出提示，不中断应用
            loading_label.text = "工程结构加载失败，请检查后端服务"
            tree_widget._props["nodes"] = []
            tree_widget.update()
            status_spinner.visible = False

    async def on_select_tree(e: ValueChangeEventArguments) -> None:
        nonlocal selected_asset, current_device_id, current_tree_node_type, current_tree_node_id
        value = e.value
        if not isinstance(value, str):
            return

        node_type: Optional[str] = None
        raw_id: Optional[str] = None
        if ":" in value:
            parts = value.split(":", 1)
            node_type, raw_id = parts[0], parts[1]
        else:
            raw_id = value

        current_tree_node_type = node_type
        current_tree_node_id = raw_id

        # 只有在设备节点上才触发资产加载
        if node_type != "device" or not raw_id:
            return

        device_id = raw_id
        current_device_id = device_id
        try:
            assets = await list_assets_for_device(device_id)
            all_assets_for_device.clear()
            for a in assets:
                enrich_asset(a)
                all_assets_for_device.append(a)
            apply_asset_filters()
            loading_label.text = ""
        except Exception:
            # 资产列表加载失败时提示用户，但不抛异常
            ui.notify("加载设备资产失败，请稍后重试", color="negative")
            loading_label.text = "资产加载失败，请检查后端服务"

    tree_widget.on_select(on_select_tree)

    # 表格行点击：点击时调用资产详情接口，加载完整数据，并自动预览图片
    async def on_asset_row_click(e: Any) -> None:
        nonlocal selected_asset

        row = e.args
        # 兼容 emit(row) 或 emit([row]) 两种情况
        if isinstance(row, list):
            if not row:
                return
            row = row[0]
        if not isinstance(row, dict):
            return

        asset_id = row.get("id")
        if not asset_id:
            return

        try:
            detail = await get_asset_detail(str(asset_id))
            enrich_asset(detail)
            selected_asset = detail
        except Exception:
            ui.notify("加载资产详情失败，请稍后重试", color="negative")
            selected_asset = row

        update_asset_detail()

        # 如果是图片资产，自动触发一次预览
        try:
            modality = (selected_asset or {}).get("modality")
            if modality == "image":
                await on_preview_click()
        except Exception:
            # 预览失败不影响基本详情展示
            pass

    asset_table.on(
        "rowClick",
        on_asset_row_click,
        js_handler="(evt, row, index) => emit(row)",
    )

    refresh_button.on_click(on_refresh_click)

    tree_search.on_value_change(lambda _: apply_tree_filter())
    modality_filter.on_value_change(lambda _: apply_asset_filters())
    role_filter.on_value_change(lambda _: apply_asset_filters())
    time_filter.on_value_change(lambda _: apply_asset_filters())

    project_select.on_value_change(reload_tree)

    async def on_create_project_click() -> None:
        """创建项目点击事件（使用新的对话框组件）"""
        if UI_COMPONENTS_ENABLED:
            # 使用新的组件
            show_create_project_dialog(
                backend_base_url=BACKEND_BASE_URL,
                on_success=reload_projects_and_tree,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                name_input = ui.input(label="项目名称")
                client_input = ui.input(label="客户")
                location_input = ui.input(label="位置")
                type_input = ui.input(label="类型")
                status_input = ui.input(label="状态")
                env_select = ui.select(
                    {
                        "": "默认环境",
                        "dev": "开发环境",
                        "test": "测试环境",
                        "prod": "生产环境",
                    },
                    value="",
                    label="环境标签",
                ).props("dense outlined")

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("保存", color="primary")

                async def do_create() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("项目名称不能为空", color="negative")
                        return

                    tags: Dict[str, Any] = {}
                    if env_select.value:
                        tags["environment"] = env_select.value

                    payload: Dict[str, Any] = {
                        "name": name,
                        "client": client_input.value or None,
                        "location": location_input.value or None,
                        "type": type_input.value or None,
                        "status": status_input.value or None,
                        "tags": tags or None,
                    }

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.post(f"{BACKEND_BASE_URL}/projects/", json=payload)
                            resp.raise_for_status()
                            data = resp.json()
                            project_id = data.get("id")
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"创建项目失败: {exc}", color="negative")
                        return

                    dialog.close()
                    ui.notify("项目创建成功", color="positive")
                    await reload_projects_and_tree(str(project_id) if project_id else None)

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_create)

            dialog.open()

    async def on_edit_project_click() -> None:
        """编辑项目点击事件（使用新的对话框组件）"""
        project = get_current_project()
        if not project:
            ui.notify("请先选择项目", color="warning")
            return

        if UI_COMPONENTS_ENABLED:
            # 使用新的组件
            show_edit_project_dialog(
                project=project,
                backend_base_url=BACKEND_BASE_URL,
                on_success=reload_projects_and_tree,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                name_input = ui.input(label="项目名称", value=project.get("name") or "")
                client_input = ui.input(label="客户", value=project.get("client") or "")
                location_input = ui.input(label="位置", value=project.get("location") or "")
                type_input = ui.input(label="类型", value=project.get("type") or "")
                status_input = ui.input(label="状态", value=project.get("status") or "")

                tags = project.get("tags") or {}
                current_env = tags.get("environment") or ""
                env_select = ui.select(
                    {
                        "": "默认环境",
                        "dev": "开发环境",
                        "test": "测试环境",
                        "prod": "生产环境",
                    },
                    value=current_env,
                    label="环境标签",
                ).props("dense outlined")

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("保存", color="primary")

                async def do_update() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("项目名称不能为空", color="negative")
                        return

                    update_tags: Dict[str, Any] = dict(tags)
                    if env_select.value:
                        update_tags["environment"] = env_select.value
                    else:
                        update_tags.pop("environment", None)

                    payload: Dict[str, Any] = {
                        "name": name,
                        "client": client_input.value or None,
                        "location": location_input.value or None,
                        "type": type_input.value or None,
                        "status": status_input.value or None,
                        "tags": update_tags or None,
                    }

                    project_id = project.get("id")
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.patch(
                                f"{BACKEND_BASE_URL}/projects/{project_id}",
                                json=payload,
                            )
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"更新项目失败: {exc}", color="negative")
                        return

                    dialog.close()
                    ui.notify("项目已更新", color="positive")
                    await reload_projects_and_tree(str(project_id) if project_id else None)

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_update)

            dialog.open()

    async def on_delete_project_click() -> None:
        project = get_current_project()
        if not project:
            ui.notify("请先选择项目", color="warning")
            return

        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label("删除项目（软删除）").classes("text-subtitle1")
            ui.label("此操作会将项目标记为已删除，但不会物理删除数据库记录。")
            reason_input = ui.input(label="删除原因")
            operator_input = ui.input(label="操作人")

            with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                cancel_btn = ui.button("取消")
                confirm_btn = ui.button("确认删除", color="negative")

            async def do_delete() -> None:
                project_id = project.get("id")
                params: Dict[str, Any] = {}
                if reason_input.value:
                    params["reason"] = reason_input.value

                headers: Dict[str, str] = {}
                if operator_input.value:
                    headers["operator"] = str(operator_input.value)

                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.delete(
                            f"{BACKEND_BASE_URL}/projects/{project_id}",
                            params=params,
                            headers=headers or None,
                        )
                        resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"删除项目失败: {exc}", color="negative")
                    return

                dialog.close()
                ui.notify("项目已删除", color="positive")
                await reload_projects_and_tree(None)

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_delete)

        dialog.open()

    async def on_run_ocr_click() -> None:
        nonlocal selected_asset
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

        inference_status_label.text = "OCR 处理中……"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{BACKEND_BASE_URL}/assets/{asset_id}/parse_image")
                resp.raise_for_status()
        except Exception as exc:
            inference_status_label.text = "OCR 失败"
            ui.notify(f"运行 OCR 失败: {exc}", color="negative")
            return

        try:
            detail = await get_asset_detail(str(asset_id))
            enrich_asset(detail)
            selected_asset = detail
        except Exception as exc:
            ui.notify(f"刷新资产详情失败: {exc}", color="negative")

        update_asset_detail()

    async def on_run_scene_llm_click() -> None:
        nonlocal selected_asset
        if not selected_asset:
            ui.notify("请先在列表中选择一个资产", color="warning")
            return

        modality = str(selected_asset.get("modality") or "").lower()
        role = str(selected_asset.get("content_role") or "").lower()
        if modality != "image":
            ui.notify("当前资产不是图片，无法提交 LLM 分析", color="warning")
            return
        if role not in {"scene_issue", "meter"}:
            ui.notify("建议对角色为 scene_issue 或 meter 的图片运行现场问题分析", color="warning")

        asset_id = selected_asset.get("id")
        if not asset_id:
            ui.notify("资产ID缺失，无法提交 LLM 分析", color="negative")
            return

        inference_status_label.text = "已提交到 LLM 管线，等待分析结果……"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{BACKEND_BASE_URL}/assets/{asset_id}/route_image")
                resp.raise_for_status()
        except Exception as exc:
            ui.notify(f"提交 LLM 分析失败: {exc}", color="negative")
            return

        try:
            detail = await get_asset_detail(str(asset_id))
            enrich_asset(detail)
            selected_asset = detail
        except Exception as exc:
            ui.notify(f"刷新资产详情失败: {exc}", color="negative")

        update_asset_detail()

    # 绑定 OCR / LLM 控制台按钮事件（需在两个 handler 定义之后）
    run_ocr_button.on_click(on_run_ocr_click)
    run_llm_button.on_click(on_run_scene_llm_click)

    async def on_upload_asset_click() -> None:
        """上传资产点击事件（使用新的对话框组件）"""
        if not project_select.value:
            ui.notify("请先选择项目", color="warning")
            return
        if not current_device_id:
            ui.notify("请先在左侧工程结构中选择一个设备节点", color="warning")
            return

        project_id = str(project_select.value)
        device_id = str(current_device_id)
        project_name = project_select.options.get(project_select.value, project_select.value)

        if UI_COMPONENTS_ENABLED:
            # 创建适配的回调函数
            async def on_upload_success(new_asset: Dict[str, Any]) -> None:
                """上传成功后的回调"""
                nonlocal all_assets_for_device
                enrich_asset(new_asset)
                all_assets_for_device.append(new_asset)
                apply_asset_filters()

            # 使用新的组件
            show_upload_asset_dialog(
                project_id=project_id,
                device_id=device_id,
                project_name=project_name,
                backend_base_url=BACKEND_BASE_URL,
                on_success=on_upload_success,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("上传图片资产").classes("text-subtitle1")
                ui.label(f"项目: {project_name}").classes("text-caption text-grey")

                role_select = ui.select(
                    {
                        "": "默认角色",
                        "meter": "仪表(meter)",
                        "scene_issue": "现场问题(scene_issue)",
                        "nameplate": "铭牌(nameplate)",
                        "energy_table": "能耗表(energy_table)",
                        "runtime_table": "运行表(runtime_table)",
                    },
                    value="",
                    label="内容角色",
                ).props("dense outlined")

                auto_route_checkbox = ui.checkbox("自动解析（OCR/LLM）", value=True)
                note_input = ui.input(label="备注").props("type=textarea")
                title_input = ui.input(label="标题（可选，默认使用文件名）")

                # 文件选择提示
                file_info_label = ui.label("尚未选择文件").classes("text-caption text-grey q-mb-sm")
                status_label = ui.label("").classes("text-caption text-grey")

                # 在 Python 端缓存已上传的单个文件内容
                selected_file: Dict[str, Any] = {"name": None, "content": None, "type": None}

                async def on_file_upload(e: events.UploadEventArguments) -> None:
                    """当浏览器将文件上传到 Python 端时缓存文件内容。"""
                    try:
                        file_bytes: bytes = b""
                        file_name: Optional[str] = None
                        file_type: Optional[str] = None

                        # 1) 旧版：e.content
                        if hasattr(e, "content") and getattr(e, "content") is not None:
                            print("[DEBUG] on_file_upload: 使用 e.content 读取")
                            content_obj = getattr(e, "content")
                            if hasattr(content_obj, "read"):
                                result = content_obj.read()
                                if inspect.iscoroutine(result):
                                    result = await result
                                file_bytes = result or b""
                            file_name = getattr(e, "name", None)
                            file_type = getattr(e, "type", None)

                        # 2) 可能存在的 e.file 属性
                        elif hasattr(e, "file") and getattr(e, "file") is not None:
                            print("[DEBUG] on_file_upload: 使用 e.file 读取")
                            file_obj = getattr(e, "file")
                            file_name = getattr(file_obj, "name", None)
                            file_type = getattr(file_obj, "type", None)
                            if hasattr(file_obj, "read"):
                                result = file_obj.read()
                                if inspect.iscoroutine(result):
                                    result = await result
                                file_bytes = result or b""

                        # 3) 新版：e.files 列表
                        elif hasattr(e, "files"):
                            files_attr = getattr(e, "files")
                            print(f"[DEBUG] on_file_upload: e.files 类型={type(files_attr)} 值={files_attr}")
                            if files_attr:
                                file_obj = files_attr[0]
                                file_name = getattr(file_obj, "name", None)
                                file_type = getattr(file_obj, "type", None)
                                if hasattr(file_obj, "read"):
                                    result = file_obj.read()
                                    if inspect.iscoroutine(result):
                                        result = await result
                                    file_bytes = result or b""
                            else:
                                print("[DEBUG] on_file_upload: e.files 为空列表")
                        else:
                            print(f"[DEBUG] on_file_upload: UploadEventArguments 无 content / file / files 属性: {e}")

                        selected_file["name"] = file_name
                        selected_file["content"] = file_bytes
                        selected_file["type"] = file_type

                        if file_bytes:
                            safe_name = file_name or "未命名文件"
                            file_info_label.text = f"已选择: {safe_name}"
                            file_info_label.classes("text-caption text-positive q-mb-sm")
                            print(f"[DEBUG] 已接收到上传文件: {safe_name}, 大小={len(file_bytes)} bytes, type={file_type}")
                        else:
                            file_info_label.text = "尚未选择文件"
                            file_info_label.classes("text-caption text-grey q-mb-sm")
                            print("[DEBUG] on_file_upload: 未能从事件中读取到任何文件字节")
                    except Exception as exc:  # noqa: BLE001
                        print(f"[DEBUG] on_file_upload 处理异常: {exc}")

                # 创建上传组件（auto_upload=True，文件到达 Python 端后触发 on_file_upload）
                upload_component = ui.upload(
                    label="选择图片文件",
                    auto_upload=True,
                    on_upload=on_file_upload,
                ).props('accept="image/*"')

                async def handle_upload() -> None:
                    # 使用在 on_file_upload 中缓存的文件内容
                    if not selected_file.get("content"):
                        ui.notify("请先选择一个文件并等待上传完成", color="warning")
                        print("[DEBUG] handle_upload: 未找到已缓存的文件内容")
                        return

                    file_name = selected_file.get("name") or "uploaded_image"
                    file_bytes = selected_file.get("content")
                    file_mime = selected_file.get("type") or "application/octet-stream"

                    print(f"[DEBUG] 开始上传文件到后端: {file_name}, size={len(file_bytes)} bytes, type={file_mime}")
                    status_label.text = "正在上传..."

                    params: Dict[str, Any] = {
                        "project_id": project_id,
                        "source": "pc_upload",
                        "device_id": device_id,
                    }
                    if role_select.value:
                        params["content_role"] = role_select.value
                    if auto_route_checkbox.value:
                        params["auto_route"] = "true"

                    data = {
                        "note": note_input.value or "",
                        "title": title_input.value or file_name,
                    }

                    files = {
                        "file": (file_name, file_bytes, file_mime)
                    }

                    try:
                        async with httpx.AsyncClient(timeout=120.0) as client:
                            resp = await client.post(
                                f"{BACKEND_BASE_URL}/assets/upload_image_with_note",
                                params=params,
                                data=data,
                                files=files,
                            )
                            resp.raise_for_status()
                            new_asset = resp.json()
                    except Exception as exc:  # noqa: BLE001
                        status_label.text = ""
                        ui.notify(f"上传失败: {exc}", color="negative")
                        return

                    enrich_asset(new_asset)
                    all_assets_for_device.append(new_asset)
                    apply_asset_filters()

                    status_label.text = ""
                    ui.notify("上传成功", color="positive")
                    # 重置已选择文件状态
                    selected_file["name"] = None
                    selected_file["content"] = None
                    selected_file["type"] = None
                    try:
                        upload_component.reset()
                    except Exception:
                        pass
                    dialog.close()

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    confirm_btn = ui.button("确认上传", color="positive")
                    cancel_btn = ui.button("取消")

                confirm_btn.on_click(handle_upload)
                cancel_btn.on_click(dialog.close)

            dialog.open()

    async def on_delete_asset_click() -> None:
        """删除资产点击事件（使用新的对话框组件）"""
        nonlocal selected_asset
        if not selected_asset:
            ui.notify("请先在列表中选择一个资产", color="warning")
            return

        asset_id = selected_asset.get("id") if selected_asset else None
        if not asset_id:
            ui.notify("资产ID缺失，无法删除", color="negative")
            return

        if UI_COMPONENTS_ENABLED:
            # 创建适配的回调函数
            async def on_delete_success(deleted_asset_id: str) -> None:
                """删除成功后的回调"""
                nonlocal selected_asset, all_assets_for_device
                # 从当前设备资产列表中移除该资产
                remaining: List[Dict[str, Any]] = [
                    a for a in all_assets_for_device if str(a.get("id")) != str(deleted_asset_id)
                ]
                all_assets_for_device.clear()
                all_assets_for_device.extend(remaining)

                selected_asset = None
                apply_asset_filters()

            # 使用新的组件
            show_delete_asset_dialog(
                asset_id=asset_id,
                backend_base_url=BACKEND_BASE_URL,
                on_success=on_delete_success,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("删除资产").classes("text-subtitle1")
                ui.label("此操作会删除资产及其解析结果。")

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("确认删除", color="negative")

                async def do_delete() -> None:
                    nonlocal selected_asset
                    asset_id_local = selected_asset.get("id") if selected_asset else None
                    if not asset_id_local:
                        ui.notify("资产ID缺失，无法删除", color="negative")
                        return

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.delete(f"{BACKEND_BASE_URL}/assets/{asset_id_local}")
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"删除资产失败: {exc}", color="negative")
                        return

                    # 从当前设备资产列表中移除该资产
                    remaining: List[Dict[str, Any]] = [
                        a for a in all_assets_for_device if str(a.get("id")) != str(asset_id_local)
                    ]
                    all_assets_for_device.clear()
                    all_assets_for_device.extend(remaining)

                    selected_asset = None
                    apply_asset_filters()

                    ui.notify("资产已删除", color="positive")
                    dialog.close()

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_delete)

            dialog.open()

    async def on_create_building_click() -> None:
        """创建楼栋点击事件（使用新的对话框组件）"""
        project = get_current_project()
        if not project:
            ui.notify("请先选择项目", color="warning")
            return

        project_id = project.get("id")

        if UI_COMPONENTS_ENABLED:
            # 使用新的组件
            show_create_building_dialog(
                project_id=project_id,
                backend_base_url=BACKEND_BASE_URL,
                on_success=reload_tree,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("新建楼栋").classes("text-subtitle1")

                name_input = ui.input(label="楼栋名称")
                usage_input = ui.input(label="用途（可选）")
                floor_area_input = ui.input(label="建筑面积 m²（可选）")
                gfa_area_input = ui.input(label="GFA 面积 m²（可选）")
                year_built_input = ui.input(label="建成年份（可选）")
                tags_input = ui.input(label="标签（逗号分隔，可选）")

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("保存", color="primary")

                async def do_create() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("楼栋名称不能为空", color="negative")
                        return

                    def parse_float(value: Any) -> Optional[float]:
                        try:
                            text = str(value).strip()
                            return float(text) if text else None
                        except Exception:
                            return None

                    floor_area = parse_float(floor_area_input.value)
                    gfa_area = parse_float(gfa_area_input.value)
                    year_built = parse_float(year_built_input.value)

                    tags_raw = (tags_input.value or "").strip()
                    tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]

                    payload: Dict[str, Any] = {
                        "name": name,
                        "usage_type": usage_input.value or None,
                        "floor_area": floor_area,
                        "gfa_area": gfa_area,
                        "year_built": year_built,
                        "tags": tags_list or None,
                    }

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.post(
                                f"{BACKEND_BASE_URL}/projects/{project_id}/buildings",
                                json=payload,
                            )
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"创建楼栋失败: {exc}", color="negative")
                        return

                    dialog.close()
                    ui.notify("楼栋创建成功", color="positive")
                    await reload_tree()

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_create)

            dialog.open()

    async def on_edit_node_click() -> None:
        """编辑楼栋点击事件（使用新的对话框组件）"""
        if current_tree_node_type != "building" or not current_tree_node_id:
            ui.notify("请先在左侧树中选择一个楼栋节点", color="warning")
            return

        building_id = current_tree_node_id

        if UI_COMPONENTS_ENABLED:
            # 使用新的组件
            show_edit_building_dialog(
                building_id=building_id,
                backend_base_url=BACKEND_BASE_URL,
                on_success=reload_tree,
            )
        else:
            # 保留旧代码作为后备
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(f"{BACKEND_BASE_URL}/buildings/{building_id}")
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"加载楼栋信息失败: {exc}", color="negative")
                return

            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("编辑楼栋").classes("text-subtitle1")

                name_input = ui.input(label="楼栋名称", value=data.get("name") or "")
                usage_input = ui.input(label="用途（可选）", value=data.get("usage_type") or "")

                def fmt_float(v: Any) -> str:
                    return "" if v is None else str(v)

                floor_area_input = ui.input(
                    label="建筑面积 m²（可选）",
                    value=fmt_float(data.get("floor_area")),
                )
                gfa_area_input = ui.input(
                    label="GFA 面积 m²（可选）",
                    value=fmt_float(data.get("gfa_area")),
                )
                year_built_input = ui.input(
                    label="建成年份（可选）",
                    value=fmt_float(data.get("year_built")),
                )

                tags_value = ""
                tags_list = data.get("tags") or []
                if isinstance(tags_list, list):
                    tags_value = ",".join(str(t) for t in tags_list)
                tags_input = ui.input(label="标签（逗号分隔，可选）", value=tags_value)

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("保存", color="primary")

                async def do_update() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("楼栋名称不能为空", color="negative")
                        return

                    def parse_float(value: Any) -> Optional[float]:
                        try:
                            text = str(value).strip()
                            return float(text) if text else None
                        except Exception:
                            return None

                    floor_area = parse_float(floor_area_input.value)
                    gfa_area = parse_float(gfa_area_input.value)
                    year_built = parse_float(year_built_input.value)

                    tags_raw = (tags_input.value or "").strip()
                    tags_list_local = [t.strip() for t in tags_raw.split(",") if t.strip()]

                    payload: Dict[str, Any] = {
                        "name": name,
                        "usage_type": usage_input.value or None,
                        "floor_area": floor_area,
                        "gfa_area": gfa_area,
                        "year_built": year_built,
                        "tags": tags_list_local or None,
                    }

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.patch(
                                f"{BACKEND_BASE_URL}/buildings/{building_id}",
                                json=payload,
                            )
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"更新楼栋失败: {exc}", color="negative")
                        return

                    dialog.close()
                    ui.notify("楼栋已更新", color="positive")
                    await reload_tree()

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_update)

            dialog.open()

    async def on_delete_node_click() -> None:
        """删除楼栋点击事件（使用新的对话框组件）"""
        if current_tree_node_type != "building" or not current_tree_node_id:
            ui.notify("请先在左侧树中选择一个楼栋节点", color="warning")
            return

        building_id = current_tree_node_id

        if UI_COMPONENTS_ENABLED:
            # 使用新的组件
            show_delete_building_dialog(
                building_id=building_id,
                backend_base_url=BACKEND_BASE_URL,
                on_success=reload_tree,
            )
        else:
            # 保留旧代码作为后备
            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("删除楼栋").classes("text-subtitle1")
                ui.label("此操作会删除楼栋及其下属结构，请谨慎操作。")

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("确认删除", color="negative")

                async def do_delete() -> None:
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.delete(f"{BACKEND_BASE_URL}/buildings/{building_id}")
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"删除楼栋失败: {exc}", color="negative")
                        return

                    ui.notify("楼栋已删除", color="positive")
                    dialog.close()
                    await reload_tree()

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_delete)

            dialog.open()

    project_create_btn.on_click(on_create_project_click)
    project_edit_btn.on_click(on_edit_project_click)
    project_delete_btn.on_click(on_delete_project_click)
    upload_asset_button.on_click(on_upload_asset_click)
    delete_asset_button.on_click(on_delete_asset_click)
    building_add_btn.on_click(on_create_building_click)
    node_edit_btn.on_click(on_edit_node_click)
    node_delete_btn.on_click(on_delete_node_click)

    async def on_preview_click() -> None:
        """在右侧详情卡片中预览图片，使用 HTTP URL 快速加载。"""
        if not selected_asset:
            ui.notify("请先选择一个资产", color="warning")
            return

        modality = selected_asset.get("modality")
        if modality != "image":
            ui.notify("当前资产不是图片，无法预览", color="warning")
            return

        rel_path = selected_asset.get("file_path")
        if not rel_path:
            ui.notify("该资产缺少文件路径信息", color="warning")
            return

        # 路径安全检查
        base_dir = os.path.abspath(SETTINGS.local_storage_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, str(rel_path)))

        try:
            common = os.path.commonpath([base_dir, abs_path])
        except ValueError:
            ui.notify("文件路径不合法", color="negative")
            return

        if common != base_dir:
            ui.notify("文件路径不合法", color="negative")
            return

        if not os.path.exists(abs_path):
            ui.notify("本地文件不存在，请检查后端存储目录", color="negative")
            return

        # 使用 HTTP URL 而不是 Data URL（性能更好，支持大文件）
        # URL 格式：/local_assets/项目ID/设备ID/文件名.png
        # 注意：需要将 Windows 路径的 \ 替换为 /
        url_path = rel_path.replace("\\", "/")
        preview_image.source = f"/local_assets/{url_path}"
        preview_image.visible = True

        print(f"[DEBUG] 预览图片: {rel_path}")
        print(f"[DEBUG] URL 路径: {url_path}")
        print(f"[DEBUG] 完整 URL: {preview_image.source}")
        print(f"[DEBUG] 文件存在: {os.path.exists(abs_path)}")
        print(f"[DEBUG] 静态目录: {SETTINGS.local_storage_dir}")
        ui.notify("图片已加载", color="positive")

    async def on_open_file_click() -> None:
        """在本机打开原始文件。仅适用于本地环境，带路径安全检查。"""
        if not selected_asset:
            ui.notify("请先选择一个资产", color="warning")
            return
        rel_path = selected_asset.get("file_path")
        if not rel_path:
            ui.notify("该资产缺少文件路径信息", color="warning")
            return

        base_dir = os.path.abspath(SETTINGS.local_storage_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, str(rel_path)))
        try:
            common = os.path.commonpath([base_dir, abs_path])
        except ValueError:
            ui.notify("文件路径不合法", color="negative")
            return
        if common != base_dir:
            ui.notify("文件路径不合法", color="negative")
            return
        if not os.path.exists(abs_path):
            ui.notify("本地文件不存在，请检查后端存储目录", color="negative")
            return
        try:
            if os.name == "nt":
                os.startfile(abs_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.call(["open", abs_path])
            else:
                subprocess.call(["xdg-open", abs_path])
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"打开文件失败: {exc}", color="negative")

    preview_button.on_click(on_preview_click)
    open_file_button.on_click(on_open_file_click)

    async def load_initial_data() -> None:
        await reload_projects_and_tree(None)

    # 使用 timer 在页面渲染后异步加载数据，避免阻塞首屏
    ui.timer(0.1, load_initial_data, once=True)
    update_asset_detail()


@ui.page("/")
def index_page() -> None:
    main_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="BDC-AI 工程结构与资产浏览", host="0.0.0.0", port=8080, dark=True)
