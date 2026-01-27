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
        self.roles_data = api_client.get_roles()
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
            permissions = role.get('permissions', [])
            formatted.append({
                'id': role.get('id'),
                'code': role.get('code'),
                'name': role.get('name'),
                'level': role.get('level'),
                'permissions_count': len(permissions),
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
        permissions = role.get('permissions', [])

        with ui.dialog() as dialog, ui.card().classes('w-md'):
            ui.label(f'{role.get("name")} - 权限列表').classes('text-xl font-bold mb-4')

            if not permissions:
                ui.label('该角色暂无权限').classes('text-gray-600')
            else:
                # 按资源分组显示权限
                permissions_by_resource = {}
                for perm in permissions:
                    code = perm.get('code', '')
                    resource = code.split(':')[0] if ':' in code else 'other'
                    if resource not in permissions_by_resource:
                        permissions_by_resource[resource] = []
                    permissions_by_resource[resource].append(perm.get('name', code))

                with ui.column().classes('gap-2'):
                    for resource, perms in sorted(permissions_by_resource.items()):
                        ui.label(f'{resource.upper()}:').classes('font-bold text-sm')
                        ui.label(', '.join(perms)).classes('text-sm text-gray-600 ml-4')

            with ui.row():
                ui.button('关闭', on_click=dialog.close).props('flat')

        dialog.open()


# 全局实例
roles_page = RolesPage()


def show_roles_page():
    """注册角色管理页面"""

    @ui.page('/admin/roles')
    def page():
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
                    {'name': 'code', 'label': '代码', 'field': 'code', 'align': 'left'},
                    {'name': 'name', 'label': '名称', 'field': 'name', 'align': 'left'},
                    {'name': 'level', 'label': '级别', 'field': 'level', 'align': 'center'},
                    {'name': 'permissions_count', 'label': '权限数量', 'field': 'permissions_count', 'align': 'center'},
                    {'name': 'description', 'label': '描述', 'field': 'description', 'align': 'left'},
                    {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'},
                ]

                def render_table():
                    rows = roles_page.format_roles_for_table()

                    # 添加操作列
                    for row in rows:
                        role_id = row['id']
                        role = next((r for r in roles_page.roles_data if r.get('id') == role_id), None)

                        actions = []
                        if role:
                            actions.append({
                                'icon': 'visibility',
                                'tooltip': '查看权限',
                                'onClick': lambda r=role: roles_page.show_role_permissions(r)
                            })
                            actions.append({
                                'icon': 'edit',
                                'tooltip': '编辑',
                                'onClick': lambda r=role: roles_page.show_edit_role_dialog(r)
                            })
                            actions.append({
                                'icon': 'delete',
                                'tooltip': '删除',
                                'onClick': lambda r=role: roles_page.show_delete_role_confirm(r)
                            })

                        row['actions'] = actions

                    roles_page.table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='id'
                    ).classes('w-full')

                render_table()
