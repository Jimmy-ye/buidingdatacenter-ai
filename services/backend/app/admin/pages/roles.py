"""
角色管理页面
"""

from nicegui import ui
from typing import Dict, Any, List
from services.backend.app.admin.services.api_client import api_client


class RolesPage:
    """角色管理页面类"""

    def __init__(self):
        self.roles_data: List[Dict[str, Any]] = []
        self.all_permissions: List[Dict[str, Any]] = []

    def load_roles(self):
        """加载角色列表"""
        print(f"[FRONTEND] Loading roles...")
        self.roles_data = api_client.get_roles()
        print(f"[FRONTEND] Loaded {len(self.roles_data)} roles")
        print(f"[FRONTEND] First role data: {self.roles_data[0] if self.roles_data else 'No data'}")
        self.refresh_table()

    def load_permissions(self):
        """加载权限列表"""
        self.all_permissions = api_client.get_permissions()

    def refresh_table(self):
        """刷新表格数据"""
        if hasattr(self, 'table'):
            self.table.rows = self.format_roles_for_table()
            self.table.update()

    def format_roles_for_table(self) -> List[Dict[str, Any]]:
        """格式化角色数据用于表格显示"""
        formatted = []
        for role in self.roles_data:
            formatted.append({
                'id': role.get('id'),
                'name': role.get('name'),  # 后端返回的是 name，不是 code
                'display_name': role.get('display_name'),
                'level': role.get('level'),
                'description': role.get('description') or '-',
            })
        return formatted

    def show_create_role_dialog(self):
        """显示创建角色对话框"""
        if not self.all_permissions:
            self.load_permissions()

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('创建新角色').classes('text-xl font-bold mb-4')

            code_input = ui.input('角色代码*', placeholder='例如: project_manager').props('outlined')
            name_input = ui.input('角色名称*', placeholder='例如: 项目经理').props('outlined')
            level_input = ui.input('级别', placeholder='例如: 60').props('outlined type="number"')
            description_input = ui.input('描述', placeholder='角色描述').props('outlined')

            # 简化版：权限选择（使用文本输入）
            ui.label('权限代码（用逗号分隔）').classes('text-sm text-gray-600 mt-2')
            permission_input = ui.input('权限', placeholder='例如: projects:read, projects:create').props('outlined')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('创建', on_click=lambda: self.handle_create_role(
                    dialog,
                    code_input.value,
                    name_input.value,
                    level_input.value,
                    description_input.value,
                    permission_input.value
                )).props('flat')

        dialog.open()

    def handle_create_role(self, dialog, code: str, name: str, level: str,
                          description: str, permissions_str: str):
        """处理创建角色"""
        if not code or not name:
            ui.notify("角色代码和名称不能为空", type="warning")
            return

        # 解析权限
        permission_codes = [p.strip() for p in permissions_str.split(',') if p.strip()] if permissions_str else []

        role_data = {
            "code": code,
            "name": name,
        }

        if level:
            try:
                role_data["level"] = int(level)
            except ValueError:
                ui.notify("级别必须是数字", type="warning")
                return

        if description:
            role_data["description"] = description

        if permission_codes:
            role_data["permission_codes"] = permission_codes

        result = api_client.create_role(role_data)
        if result and "error" not in result:
            dialog.close()
            self.load_roles()

    def show_edit_role_dialog(self, role: Dict[str, Any]):
        """显示编辑角色对话框"""
        if not self.all_permissions:
            self.load_permissions()

        # 获取当前权限代码
        current_permissions = [p.get('code') for p in role.get('permissions', [])]
        permissions_str = ', '.join(current_permissions)

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('编辑角色').classes('text-xl font-bold mb-4')

            name_input = ui.input('角色名称*', value=role.get('name', '')).props('outlined')
            level_input = ui.input('级别', value=str(role.get('level', ''))).props('outlined type="number"')
            description_input = ui.input('描述', value=role.get('description', '') or '').props('outlined')

            # 权限显示和编辑
            ui.label('当前权限代码（用逗号分隔）').classes('text-sm text-gray-600 mt-2')
            permission_input = ui.input('权限', value=permissions_str, placeholder='例如: projects:read').props('outlined')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=lambda: self.handle_update_role(
                    dialog,
                    role.get('id'),
                    name_input.value,
                    level_input.value,
                    description_input.value,
                    permission_input.value
                )).props('flat')

        dialog.open()

    def handle_update_role(self, dialog, role_id: str, name: str, level: str,
                          description: str, permissions_str: str):
        """处理更新角色"""
        role_data = {}

        if name:
            role_data["name"] = name

        if level:
            try:
                role_data["level"] = int(level)
            except ValueError:
                ui.notify("级别必须是数字", type="warning")
                return

        if description:
            role_data["description"] = description

        # 解析权限
        if permissions_str:
            permission_codes = [p.strip() for p in permissions_str.split(',') if p.strip()]
            role_data["permission_codes"] = permission_codes

        if api_client.update_role(role_id, role_data):
            dialog.close()
            self.load_roles()

    def show_delete_role_confirm(self, role: Dict[str, Any]):
        """显示删除角色确认对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('确认删除').classes('text-xl font-bold mb-4')
            ui.label(f"确定要删除角色 '{role.get('name')}' 吗？").classes('mb-4')
            ui.label("此操作不可恢复！").classes('text-red-600 mb-4')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认删除', on_click=lambda: self.handle_delete_role(dialog, role.get('id'))).props('flat bg-red-600 text-white')

        dialog.open()

    def handle_delete_role(self, dialog, role_id: str):
        """处理删除角色"""
        if api_client.delete_role(role_id):
            dialog.close()
            self.load_roles()

    def show_role_permissions(self, role: Dict[str, Any]):
        """显示角色权限详情"""
        # 调用详情端点获取完整信息（包括权限）
        role_detail = api_client.get_role(role.get('id'))

        if not role_detail or "error" in role_detail:
            ui.notify("获取角色权限失败", type="negative")
            return

        permissions = role_detail.get('permissions', [])

        with ui.dialog() as dialog, ui.card().classes('w-md'):
            ui.label(f'{role.get("display_name") or role.get("name")} - 权限列表').classes('text-xl font-bold mb-4')

            if not permissions:
                ui.label('该角色暂无权限').classes('text-gray-600')
            else:
                # 显示权限代码列表
                with ui.column().classes('gap-1'):
                    for perm_code in permissions:
                        ui.label(f'• {perm_code}').classes('text-sm text-gray-600')

            with ui.row():
                ui.button('关闭', on_click=dialog.close).props('flat')

        dialog.open()


# 全局实例
roles_page = RolesPage()


def show_roles_page():
    """注册角色管理页面"""

    @ui.page('/admin/roles')
    def page():
        try:
            print(f"[FRONTEND] /admin/roles page called")
            # 加载数据
            roles_page.load_roles()
            roles_page.load_permissions()

            with ui.column().classes('w-full p-4 gap-4'):
                # 标题和操作栏
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('角色管理').classes('text-2xl font-bold')

                with ui.row():
                    ui.button(icon='refresh', on_click=roles_page.load_roles).props('flat').tooltip('刷新')
                    ui.button('➕ 创建角色', on_click=roles_page.show_create_role_dialog).props('flat')

                # 统计信息
                ui.label(f'共 {len(roles_page.roles_data)} 个角色').classes('text-gray-600')

                # 角色列表表格
                with ui.card().classes('w-full'):
                    columns = [
                        {'name': 'name', 'label': '角色名', 'field': 'name', 'align': 'left'},
                        {'name': 'display_name', 'label': '显示名', 'field': 'display_name', 'align': 'left'},
                        {'name': 'level', 'label': '级别', 'field': 'level', 'align': 'center'},
                        {'name': 'description', 'label': '描述', 'field': 'description', 'align': 'left'},
                        {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'},
                    ]

                    def render_table():
                        try:
                            print(f"[FRONTEND] Rendering table with {len(roles_page.roles_data)} roles")
                            rows = roles_page.format_roles_for_table()
                            print(f"[FRONTEND] Formatted {len(rows)} rows for table")
                            roles_page.table = ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id'
                            ).classes('w-full')

                            @roles_page.table.add_slot('body-cell-actions')
                            def _(row):
                                try:
                                    role_id = row.get('id')
                                    role = next((r for r in roles_page.roles_data if r.get('id') == role_id), None)
                                    if not role:
                                        return

                                    with ui.row().classes('items-center justify-center gap-1'):
                                        ui.button(
                                            icon='edit',
                                            on_click=lambda r=role: roles_page.show_edit_role_dialog(r)
                                        ).props('flat round dense').tooltip('编辑')
                                        ui.button(
                                            icon='delete',
                                            on_click=lambda r=role: roles_page.show_delete_role_confirm(r)
                                        ).props('flat round dense color=red').tooltip('删除')
                                except Exception as e:
                                    print(f"[FRONTEND ERROR] role actions cell render failed: {e}")

                            print(f"[FRONTEND] Table created successfully with actions slot")
                        except Exception as e:
                            print(f"[FRONTEND ERROR] Table rendering failed: {e}")
                            import traceback
                            traceback.print_exc()
                            ui.label(f'表格渲染错误: {str(e)}').classes('text-red-600')

                    render_table()

        except Exception as e:
            print(f"[FRONTEND ERROR] Page rendering failed: {e}")
            import traceback
            traceback.print_exc()
            ui.label(f'页面加载错误: {str(e)}').classes('text-red-600')
