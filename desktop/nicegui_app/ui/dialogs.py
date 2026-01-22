"""
对话框组件模块

提供可复用的对话框组件

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Callable, Dict, Optional
import httpx
from nicegui import ui


# ==================== 项目对话框组件 ====================

class ProjectDialog:
    """
    项目对话框组件

    封装创建和编辑项目的对话框逻辑
    """

    def __init__(
        self,
        backend_base_url: str = "http://127.0.0.1:8000/api/v1",
        on_success: Optional[Callable[[str], None]] = None,
    ):
        """
        初始化项目对话框

        Args:
            backend_base_url: 后端 API 基础 URL
            on_success: 成功回调，接收项目 ID
        """
        self.backend_base_url = backend_base_url
        self.on_success = on_success

    def show_create(self) -> None:
        """显示创建项目对话框"""
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
                """执行创建项目"""
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
                        resp = await client.post(
                            f"{self.backend_base_url}/projects/",
                            json=payload
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        project_id = data.get("id")
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"创建项目失败: {exc}", color="negative")
                    return

                dialog.close()
                ui.notify("项目创建成功", color="positive")

                if self.on_success and project_id:
                    await self.on_success(str(project_id))

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_create)

        dialog.open()

    def show_edit(self, project: Dict[str, Any]) -> None:
        """
        显示编辑项目对话框

        Args:
            project: 项目数据
        """
        dialog = ui.dialog()
        with dialog, ui.card():
            name_input = ui.input(
                label="项目名称",
                value=project.get("name") or ""
            )
            client_input = ui.input(
                label="客户",
                value=project.get("client") or ""
            )
            location_input = ui.input(
                label="位置",
                value=project.get("location") or ""
            )
            type_input = ui.input(
                label="类型",
                value=project.get("type") or ""
            )
            status_input = ui.input(
                label="状态",
                value=project.get("status") or ""
            )

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
                """执行更新项目"""
                name = (name_input.value or "").strip()
                if not name:
                    ui.notify("项目名称不能为空", color="negative")
                    return

                update_tags: Dict[str, Any] = dict(tags)
                if env_select.value:
                    update_tags["environment"] = env_select.value
                elif "environment" in update_tags:
                    del update_tags["environment"]

                payload: Dict[str, Any] = {
                    "name": name,
                    "client": client_input.value or None,
                    "location": location_input.value or None,
                    "type": type_input.value or None,
                    "status": status_input.value or None,
                    "tags": update_tags or None,
                }

                try:
                    project_id = project.get("id")
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.patch(
                            f"{self.backend_base_url}/projects/{project_id}",
                            json=payload
                        )
                        resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"更新项目失败: {exc}", color="negative")
                    return

                dialog.close()
                ui.notify("项目已更新", color="positive")

                if self.on_success:
                    await self.on_success(str(project_id))

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_update)

        dialog.open()


# ==================== 便捷函数 ====================

def show_create_project_dialog(
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable[[str], None]] = None,
) -> ProjectDialog:
    """
    显示创建项目对话框（便捷函数）

    Args:
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        ProjectDialog 实例
    """
    dialog = ProjectDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_create()
    return dialog


def show_edit_project_dialog(
    project: Dict[str, Any],
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable[[str], None]] = None,
) -> ProjectDialog:
    """
    显示编辑项目对话框（便捷函数）

    Args:
        project: 项目数据
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        ProjectDialog 实例
    """
    dialog = ProjectDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_edit(project)
    return dialog


# ==================== 工程结构节点对话框组件 ====================

class EngineeringNodeDialog:
    """
    工程结构节点对话框组件

    封装创建、编辑、删除楼栋等节点的对话框逻辑
    """

    def __init__(
        self,
        backend_base_url: str = "http://127.0.0.1:8000/api/v1",
        on_success: Optional[Callable] = None,
    ):
        """
        初始化工程节点对话框

        Args:
            backend_base_url: 后端 API 基础 URL
            on_success: 成功回调
        """
        self.backend_base_url = backend_base_url
        self.on_success = on_success

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """解析浮点数"""
        try:
            text = str(value).strip()
            return float(text) if text else None
        except Exception:
            return None

    @staticmethod
    def _format_float(v: Any) -> str:
        """格式化浮点数为字符串"""
        return "" if v is None else str(v)

    def show_create_building(
        self,
        project_id: str,
        project_name: Optional[str] = None,
    ) -> None:
        """
        显示创建楼栋对话框

        Args:
            project_id: 项目 ID
            project_name: 项目名称（可选，用于显示）
        """
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
                """执行创建楼栋"""
                name = (name_input.value or "").strip()
                if not name:
                    ui.notify("楼栋名称不能为空", color="negative")
                    return

                floor_area = self._parse_float(floor_area_input.value)
                gfa_area = self._parse_float(gfa_area_input.value)
                year_built = self._parse_float(year_built_input.value)

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
                            f"{self.backend_base_url}/projects/{project_id}/buildings",
                            json=payload,
                        )
                        resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"创建楼栋失败: {exc}", color="negative")
                    return

                dialog.close()
                ui.notify("楼栋创建成功", color="positive")

                if self.on_success:
                    await self.on_success()

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_create)

        dialog.open()

    def show_edit_building(
        self,
        building_id: str,
    ) -> None:
        """
        显示编辑楼栋对话框

        Args:
            building_id: 楼栋 ID
        """
        # 先加载楼栋信息
        import asyncio

        async def load_and_show():
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(
                        f"{self.backend_base_url}/buildings/{building_id}"
                    )
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as exc:  # noqa: BLE001
                ui.notify(f"加载楼栋信息失败: {exc}", color="negative")
                return

            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label("编辑楼栋").classes("text-subtitle1")

                name_input = ui.input(
                    label="楼栋名称",
                    value=data.get("name") or ""
                )
                usage_input = ui.input(
                    label="用途（可选）",
                    value=data.get("usage_type") or ""
                )
                floor_area_input = ui.input(
                    label="建筑面积 m²（可选）",
                    value=self._format_float(data.get("floor_area")),
                )
                gfa_area_input = ui.input(
                    label="GFA 面积 m²（可选）",
                    value=self._format_float(data.get("gfa_area")),
                )
                year_built_input = ui.input(
                    label="建成年份（可选）",
                    value=self._format_float(data.get("year_built")),
                )

                tags_value = ""
                tags_list = data.get("tags") or []
                if isinstance(tags_list, list):
                    tags_value = ",".join(str(t) for t in tags_list)
                tags_input = ui.input(
                    label="标签（逗号分隔，可选）",
                    value=tags_value
                )

                with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                    cancel_btn = ui.button("取消")
                    confirm_btn = ui.button("保存", color="primary")

                async def do_update() -> None:
                    """执行更新楼栋"""
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("楼栋名称不能为空", color="negative")
                        return

                    floor_area = self._parse_float(floor_area_input.value)
                    gfa_area = self._parse_float(gfa_area_input.value)
                    year_built = self._parse_float(year_built_input.value)

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
                                f"{self.backend_base_url}/buildings/{building_id}",
                                json=payload,
                            )
                            resp.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"更新楼栋失败: {exc}", color="negative")
                        return

                    dialog.close()
                    ui.notify("楼栋已更新", color="positive")

                    if self.on_success:
                        await self.on_success()

                cancel_btn.on_click(dialog.close)
                confirm_btn.on_click(do_update)

            dialog.open()

        # 在 NiceGUI 上下文中运行异步函数
        asyncio.create_task(load_and_show())

    def show_delete_building(
        self,
        building_id: str,
    ) -> None:
        """
        显示删除楼栋确认对话框

        Args:
            building_id: 楼栋 ID
        """
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label("删除楼栋").classes("text-subtitle1")
            ui.label("此操作会删除楼栋及其下属结构，请谨慎操作。")

            with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                cancel_btn = ui.button("取消")
                confirm_btn = ui.button("确认删除", color="negative")

            async def do_delete() -> None:
                """执行删除楼栋"""
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.delete(
                            f"{self.backend_base_url}/buildings/{building_id}"
                        )
                        resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"删除楼栋失败: {exc}", color="negative")
                    return

                ui.notify("楼栋已删除", color="positive")
                dialog.close()

                if self.on_success:
                    await self.on_success()

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_delete)

        dialog.open()


# ==================== 便捷函数 ====================

def show_create_building_dialog(
    project_id: str,
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable] = None,
) -> EngineeringNodeDialog:
    """
    显示创建楼栋对话框（便捷函数）

    Args:
        project_id: 项目 ID
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        EngineeringNodeDialog 实例
    """
    dialog = EngineeringNodeDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_create_building(project_id)
    return dialog


def show_edit_building_dialog(
    building_id: str,
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable] = None,
) -> EngineeringNodeDialog:
    """
    显示编辑楼栋对话框（便捷函数）

    Args:
        building_id: 楼栋 ID
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        EngineeringNodeDialog 实例
    """
    dialog = EngineeringNodeDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_edit_building(building_id)
    return dialog


def show_delete_building_dialog(
    building_id: str,
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable] = None,
) -> EngineeringNodeDialog:
    """
    显示删除楼栋确认对话框（便捷函数）

    Args:
        building_id: 楼栋 ID
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        EngineeringNodeDialog 实例
    """
    dialog = EngineeringNodeDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_delete_building(building_id)
    return dialog


# ==================== 资产对话框组件 ====================

class AssetDialog:
    """
    资产对话框组件

    封装上传、删除资产的对话框逻辑
    """

    def __init__(
        self,
        backend_base_url: str = "http://127.0.0.1:8000/api/v1",
        on_success: Optional[Callable] = None,
    ):
        """
        初始化资产对话框

        Args:
            backend_base_url: 后端 API 基础 URL
            on_success: 成功回调
        """
        self.backend_base_url = backend_base_url
        self.on_success = on_success

    def show_upload_image(
        self,
        project_id: str,
        device_id: str,
        project_name: Optional[str] = None,
    ) -> None:
        """
        显示上传图片资产对话框

        Args:
            project_id: 项目 ID
            device_id: 设备 ID
            project_name: 项目名称（可选，用于显示）
        """
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label("上传图片资产").classes("text-subtitle1")
            if project_name:
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

            async def on_file_upload(e: Any) -> None:
                """当浏览器将文件上传到 Python 端时缓存文件内容"""
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
                """执行上传"""
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
                    "project_id": str(project_id),
                    "source": "pc_upload",
                    "device_id": str(device_id),
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
                            f"{self.backend_base_url}/assets/upload_image_with_note",
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

                # 调用成功回调（如果提供）
                if self.on_success:
                    await self.on_success(new_asset)

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

    def show_delete_asset(
        self,
        asset_id: str,
    ) -> None:
        """
        显示删除资产确认对话框

        Args:
            asset_id: 资产 ID
        """
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label("删除资产").classes("text-subtitle1")
            ui.label("此操作会删除资产及其解析结果。")

            with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
                cancel_btn = ui.button("取消")
                confirm_btn = ui.button("确认删除", color="negative")

            async def do_delete() -> None:
                """执行删除资产"""
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.delete(f"{self.backend_base_url}/assets/{asset_id}")
                        resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    ui.notify(f"删除资产失败: {exc}", color="negative")
                    return

                ui.notify("资产已删除", color="positive")
                dialog.close()

                # 调用成功回调（如果提供）
                if self.on_success:
                    await self.on_success(asset_id)

            cancel_btn.on_click(dialog.close)
            confirm_btn.on_click(do_delete)

        dialog.open()


# ==================== 便捷函数 ====================

def show_upload_asset_dialog(
    project_id: str,
    device_id: str,
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable] = None,
) -> AssetDialog:
    """
    显示上传资产对话框（便捷函数）

    Args:
        project_id: 项目 ID
        device_id: 设备 ID
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        AssetDialog 实例
    """
    dialog = AssetDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_upload_image(project_id, device_id)
    return dialog


def show_delete_asset_dialog(
    asset_id: str,
    backend_base_url: str = "http://127.0.0.1:8000/api/v1",
    on_success: Optional[Callable] = None,
) -> AssetDialog:
    """
    显示删除资产确认对话框（便捷函数）

    Args:
        asset_id: 资产 ID
        backend_base_url: 后端 API 基础 URL
        on_success: 成功回调

    Returns:
        AssetDialog 实例
    """
    dialog = AssetDialog(
        backend_base_url=backend_base_url,
        on_success=on_success,
    )
    dialog.show_delete_asset(asset_id)
    return dialog
