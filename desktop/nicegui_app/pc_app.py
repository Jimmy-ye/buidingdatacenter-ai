from __future__ import annotations

import base64
import os
import subprocess
import sys
from datetime import datetime, timedelta
from mimetypes import guess_type
from typing import Any, Dict, List, Optional

import httpx
from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from shared.config.settings import get_settings

BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1"
SETTINGS = get_settings()


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
    return await fetch_json(f"/devices/{device_id}/assets")


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
        # 左侧：工程结构树
        with ui.card().style("width: 320px; height: 100%; overflow: auto;"):
            ui.label("工程结构").classes("text-h6")

            project_select = ui.select({}, value=None, label="项目")
            tree_search = ui.input(placeholder="搜索结构名称...").props("dense clearable").classes("q-mt-sm")
            tree_widget = ui.tree([]).props("node-key=id")

        # 右侧：顶部项目信息 + 资产列表 / 详情两列布局
        with ui.column().style("flex-grow: 1; height: 100%; overflow: auto;"):
            with ui.column().classes("q-pa-md"):
                with ui.row().classes("items-center justify-between w-full"):
                    project_title = ui.label("未选择项目").classes("text-h6")
                    refresh_button = ui.button(icon="refresh").props("flat round dense")
                project_meta = ui.label("").classes("text-caption text-grey")

                ui.separator()

                with ui.row().classes("w-full q-mt-md items-start"):
                    # 左列：资产过滤器 + 列表（约 40% 宽度）
                    with ui.column().style("min-width: 40%; max-width: 40%;"):
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
                                    "style": "width: 140px;",
                                },
                            ],
                            rows=[],
                        ).props('row-key="id" dense flat').classes("w-full")

                    # 右列：资产详情 + 图片预览 + OCR/LLM 结果（剩余宽度）
                    with ui.column().style("flex-grow: 1; min-width: 0; overflow: hidden;"):
                        with ui.card().classes("w-full"):
                            ui.label("基本信息").classes("text-subtitle2 q-mb-sm")
                            detail_title = ui.label("资产详情").classes("text-subtitle1")
                            detail_meta = ui.label("").classes("text-caption text-grey q-mb-xs")
                            detail_body = ui.label("请选择左侧设备，加载资产后查看详情。").classes("text-body2").style("word-break: break-word;")
                            detail_tags = ui.label("").classes("text-caption text-grey")

                        with ui.card().classes("w-full q-mt-sm"):
                            ui.label("图片预览").classes("text-subtitle2 q-mb-sm")
                            with ui.row().classes("items-center justify-center"):
                                preview_image = ui.image().style(
                                    "max-width: 400px; max-height: 260px; object-fit: contain;"
                                )
                                preview_image.visible = False
                            with ui.row().classes("q-mt-sm q-gutter-sm"):
                                preview_button = ui.button("预览图片")
                                open_file_button = ui.button("打开原始文件")

                        with ui.card().classes("w-full q-mt-sm"):
                            ui.label("OCR/LLM 识别结果").classes("text-subtitle2 q-mb-sm")
                            ocr_objects_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word;")
                            ocr_text_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word;")
                            llm_summary_label = ui.label("").classes("text-body2").style("white-space: pre-wrap; word-break: break-word;")

    projects_cache: List[Dict[str, Any]] = []
    full_tree_nodes: List[Dict[str, Any]] = []
    selected_asset: Optional[Dict[str, Any]] = None
    all_assets_for_device: List[Dict[str, Any]] = []

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
        # preview_image.visible = False  # 移除这行
        if str(modality).lower() == "image":
            preview_button.disabled = False
        else:
            preview_button.disabled = True

        # 填充 OCR/LLM 识别结果区域
        ocr_objects_label.text = ""
        ocr_text_label.text = ""
        llm_summary_label.text = ""

        # 从 structured_payloads 数组中提取数据
        payloads = asset.get("structured_payloads") or []
        for sp in payloads:
            schema = sp.get("schema_type", "")
            data = sp.get("payload", {})

            # 图片 OCR 识别结果
            if schema == "image_annotation":
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

        previous_id = selected_asset.get("id") if isinstance(selected_asset, dict) else None
        preserved = None
        if previous_id is not None:
            for a in filtered:
                if a.get("id") == previous_id:
                    preserved = a
                    break
        if preserved is not None:
            selected_asset = preserved
        else:
            selected_asset = filtered[0] if filtered else None
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
        nonlocal selected_asset
        # 切换项目或刷新结构树时，重置资产相关状态
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
        nonlocal selected_asset
        value = e.value
        if not isinstance(value, str):
            return
        # 约定 id 形如 "device:<uuid>"，只在设备节点上触发资产加载
        if not value.startswith("device:"):
            return
        device_id = value.split(":", 1)[1]
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

    # 表格行点击：使用 NiceGUI 的通用事件接口 + js_handler 直接拿到 row
    def on_asset_row_click(e: Any) -> None:
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

        # 从 all_assets_for_device 中找到完整资产对象（包含 file_path 等字段）
        for asset in all_assets_for_device:
            if str(asset.get("id")) == str(asset_id):
                selected_asset = asset
                print(f"[Asset] 选中资产: {asset.get('title')} (ID: {asset_id})")
                break
        else:
            # 兜底：直接用行数据
            selected_asset = row

        update_asset_detail()

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

    async def on_preview_click() -> None:
        """在右侧详情中预览图片（通过 data URL 内嵌），带路径安全检查。"""
        print(f"[DEBUG] 预览按钮被点击")
        print(f"[DEBUG] selected_asset: {selected_asset}")

        if not selected_asset:
            print("[DEBUG] selected_asset为空")
            ui.notify("请先选择一个资产", color="warning")
            return

        modality = selected_asset.get("modality")
        print(f"[DEBUG] modality: {modality}")

        if modality != "image":
            print(f"[DEBUG] 不是图片类型，无法预览")
            ui.notify("当前资产不是图片，无法预览", color="warning")
            return

        rel_path = selected_asset.get("file_path")
        print(f"[DEBUG] file_path: {rel_path}")

        if not rel_path:
            print("[DEBUG] file_path为空")
            ui.notify("该资产缺少文件路径信息", color="warning")
            return

        base_dir = os.path.abspath(SETTINGS.local_storage_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, str(rel_path)))
        print(f"[DEBUG] base_dir: {base_dir}")
        print(f"[DEBUG] abs_path: {abs_path}")
        print(f"[DEBUG] 文件存在: {os.path.exists(abs_path)}")

        try:
            common = os.path.commonpath([base_dir, abs_path])
        except ValueError:
            print("[DEBUG] 路径验证失败: ValueError")
            ui.notify("文件路径不合法", color="negative")
            return

        if common != base_dir:
            print(f"[DEBUG] 路径验证失败: common={common}, base_dir={base_dir}")
            ui.notify("文件路径不合法", color="negative")
            return

        if not os.path.exists(abs_path):
            print("[DEBUG] 文件不存在")
            ui.notify("本地文件不存在，请检查后端存储目录", color="negative")
            return

        mime_type, _ = guess_type(abs_path)
        if mime_type is None:
            mime_type = "image/jpeg"
        print(f"[DEBUG] mime_type: {mime_type}")

        try:
            with open(abs_path, "rb") as f:
                data = f.read()
            print(f"[DEBUG] 成功读取文件，大小: {len(data)} bytes")
        except Exception as exc:  # noqa: BLE001
            print(f"[DEBUG] 读取文件失败: {exc}")
            ui.notify(f"读取图片失败: {exc}", color="negative")
            return

        b64 = base64.b64encode(data).decode("ascii")
        preview_image.source = f"data:{mime_type};base64,{b64}"
        preview_image.visible = True
        print(f"[DEBUG] 预览图已设置，visible=True")
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
        nonlocal projects_cache
        status_spinner.visible = True
        projects = await list_projects()
        if not projects:
            loading_label.text = "暂无项目，请先在后端创建项目"
            status_spinner.visible = False
            return

        projects_cache = projects
        options = {p["id"]: p["name"] for p in projects}
        project_select.options = options
        project_select.value = projects[0]["id"]
        loading_label.text = ""
        status_spinner.visible = False
        update_project_header()
        await reload_tree()

    # 使用 timer 在页面渲染后异步加载数据，避免阻塞首屏
    ui.timer(0.1, load_initial_data, once=True)
    update_asset_detail()


@ui.page("/")
def index_page() -> None:
    main_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="BDC-AI 工程结构与资产浏览", host="0.0.0.0", port=8080, dark=True)
