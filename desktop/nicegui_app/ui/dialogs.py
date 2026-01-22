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
