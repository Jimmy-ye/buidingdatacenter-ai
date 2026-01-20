from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from nicegui import ui
from nicegui.events import ValueChangeEventArguments

BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1"


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

    with ui.row().style("height: 100vh; width: 100vw;"):
        # 左侧：工程结构树
        with ui.card().style("width: 320px; height: 100%; overflow: auto;"):
            ui.label("工程结构").classes("text-h6")

            project_select = ui.select({}, value=None, label="项目")
            tree_widget = ui.tree([]).props("node-key=id")

        # 右侧：顶部项目信息 + 资产列表 + 资产详情
        with ui.column().style("flex-grow: 1; height: 100%; overflow: auto;"):
            with ui.column().classes("q-pa-md"):
                with ui.row().classes("items-center justify-between w-full"):
                    project_title = ui.label("未选择项目").classes("text-h6")
                    refresh_button = ui.button(icon="refresh").props("flat round dense")
                project_meta = ui.label("").classes("text-caption text-grey")

            ui.separator()
            ui.label("资产列表").classes("text-subtitle1 q-mt-md")

            asset_table = ui.table(
                columns=[
                    {"name": "id", "label": "ID", "field": "id"},
                    {"name": "modality", "label": "类型", "field": "modality"},
                    {"name": "content_role", "label": "角色", "field": "content_role"},
                    {"name": "capture_time", "label": "采集时间", "field": "capture_time"},
                ],
                rows=[],
            ).classes("w-full")

            detail_title = ui.label("资产详情").classes("text-subtitle1 q-mt-md")
            detail_meta = ui.label("").classes("text-caption text-grey")
            detail_body = ui.label("请选择左侧设备，加载资产后查看详情。").classes("text-body2")
            detail_tags = ui.label("").classes("text-caption text-grey")

    projects_cache: List[Dict[str, Any]] = []
    selected_asset: Optional[Dict[str, Any]] = None

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

    async def on_refresh_click() -> None:
        nonlocal selected_asset
        loading_label.text = "正在刷新工程结构..."
        asset_table.rows = []
        asset_table.update()
        selected_asset = None
        update_asset_detail()
        await reload_tree()

    async def reload_tree() -> None:
        update_project_header()
        if not project_select.value:
            tree_widget._props["nodes"] = []
            tree_widget.update()
            return
        try:
            data = await get_structure_tree(str(project_select.value))
            nodes = build_tree_nodes(data)
            tree_widget._props["nodes"] = nodes
            tree_widget.update()
            loading_label.text = ""
        except Exception:
            # 后端不可用或结构树接口异常时，仅在页面上给出提示，不中断应用
            loading_label.text = "工程结构加载失败，请检查后端服务"
            tree_widget._props["nodes"] = []
            tree_widget.update()

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
            asset_table.rows = assets
            asset_table.update()
            selected_asset = assets[0] if assets else None
            update_asset_detail()
        except Exception:
            # 资产列表加载失败时提示用户，但不抛异常
            ui.notify("加载设备资产失败，请稍后重试", color="negative")

    tree_widget.on_select(on_select_tree)

    async def on_asset_row_click(e: Any) -> None:
        nonlocal selected_asset
        # 兼容多种可能的 e.args 格式：
        # 1) 直接是行 dict
        # 2) 带有 "row" 键的 dict
        # 3) [row, index] 列表/元组
        args = getattr(e, "args", None)
        row: Any = None
        if isinstance(args, dict):
            if "row" in args and isinstance(args["row"], dict):
                row = args["row"]
            else:
                # 有可能直接就是行对象
                row = args
        elif isinstance(args, (list, tuple)) and args:
            candidate = args[0]
            if isinstance(candidate, dict):
                row = candidate

        if not isinstance(row, dict):
            return

        selected_asset = row
        update_asset_detail()

    # bind to underlying Quasar table rowClick event
    asset_table.on("rowClick", on_asset_row_click)

    refresh_button.on_click(on_refresh_click)

    project_select.on_value_change(reload_tree)

    async def load_initial_data() -> None:
        nonlocal projects_cache
        projects = await list_projects()
        if not projects:
            loading_label.text = "暂无项目，请先在后端创建项目"
            return

        projects_cache = projects
        options = {p["id"]: p["name"] for p in projects}
        project_select.options = options
        project_select.value = projects[0]["id"]
        loading_label.text = ""
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
