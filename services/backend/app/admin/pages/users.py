"""
用户管理页面
"""

from nicegui import ui
from typing import Dict, Any, List
from services.backend.app.admin.services.api_client import api_client


class UsersPage:
    """用户管理页面类"""

    def __init__(self):
        self.users_data: List[Dict[str, Any]] = []
        self.current_page = 0
        self.page_size = 20

    def load_users(self):
        """加载用户列表"""
        self.users_data = api_client.get_users(
            skip=self.current_page * self.page_size,
            limit=self.page_size
        )
        self.refresh_table()

    def refresh_table(self):
        """刷新表格数据"""
        if hasattr(self, 'table'):
            self.table.props('rows-per-page-options=[20,50,100]')
            self.table.rows = self.format_users_for_table()
            self.table.update()

    def format_users_for_table(self) -> List[Dict[str, Any]]:
        """格式化用户数据用于表格显示"""
        formatted = []
        for user in self.users_data:
            roles_str = ', '.join([r.get('name', r.get('code', '?')) for r in user.get('roles', [])])
            formatted.append({
                'id': user.get('id'),
                'username': user.get('username'),
                'full_name': user.get('full_name') or '-',
                'email': user.get('email') or '-',
                'roles': roles_str,
                'is_active': '✓' if user.get('is_active') else '✗',
                'created_at': user.get('created_at', '-')[:10] if user.get('created_at') else '-',
            })
        return formatted

    def show_create_user_dialog(self):
        """显示创建用户对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('创建新用户').classes('text-xl font-bold mb-4')

            username_input = ui.input('用户名*', placeholder='请输入用户名').props('outlined')
            full_name_input = ui.input('姓名', placeholder='请输入姓名').props('outlined')
            email_input = ui.input('邮箱', placeholder='请输入邮箱').props('outlined')
            password_input = ui.input('密码*', placeholder='请输入密码', password=True, password_toggle_button=True).props('outlined')
            phone_input = ui.input('电话', placeholder='请输入电话').props('outlined')

            # 角色选择（简化版，使用文本输入）
            role_input = ui.input('角色（用逗号分隔）', placeholder='例如: admin, user').props('outlined')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('创建', on_click=lambda: self.handle_create_user(
                    dialog,
                    username_input.value,
                    full_name_input.value,
                    email_input.value,
                    password_input.value,
                    phone_input.value,
                    role_input.value
                )).props('flat')

        dialog.open()

    def handle_create_user(self, dialog, username: str, full_name: str, email: str,
                          password: str, phone: str, roles_str: str):
        """处理创建用户"""
        if not username or not password:
            ui.notify("用户名和密码不能为空", type="warning")
            return

        # 解析角色
        role_codes = [r.strip() for r in roles_str.split(',') if r.strip()] if roles_str else []

        user_data = {
            "username": username,
            "password": password,
        }

        if full_name:
            user_data["full_name"] = full_name
        if email:
            user_data["email"] = email
        if phone:
            user_data["phone"] = phone
        if role_codes:
            user_data["role_codes"] = role_codes

        result = api_client.create_user(user_data)
        if result and "error" not in result:
            dialog.close()
            self.load_users()

    def show_edit_user_dialog(self, user: Dict[str, Any]):
        """显示编辑用户对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('编辑用户').classes('text-xl font-bold mb-4')

            full_name_input = ui.input('姓名', value=user.get('full_name') or '').props('outlined')
            email_input = ui.input('邮箱', value=user.get('email') or '').props('outlined')
            phone_input = ui.input('电话', value=user.get('phone') or '').props('outlined')

            # 角色显示（简化版）
            current_roles = ', '.join([r.get('name', r.get('code', '?')) for r in user.get('roles', [])])
            ui.label(f'当前角色: {current_roles or "无"}').classes('text-sm text-gray-600 mb-2')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=lambda: self.handle_update_user(
                    dialog,
                    user.get('id'),
                    full_name_input.value,
                    email_input.value,
                    phone_input.value
                )).props('flat')

        dialog.open()

    def handle_update_user(self, dialog, user_id: str, full_name: str, email: str, phone: str):
        """处理更新用户"""
        user_data = {}

        if full_name:
            user_data["full_name"] = full_name
        if email:
            user_data["email"] = email
        if phone:
            user_data["phone"] = phone

        if api_client.update_user(user_id, user_data):
            dialog.close()
            self.load_users()

    def show_delete_user_confirm(self, user: Dict[str, Any]):
        """显示删除用户确认对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('确认删除').classes('text-xl font-bold mb-4')
            ui.label(f"确定要删除用户 '{user.get('username')}' 吗？").classes('mb-4')
            ui.label("此操作不可恢复！").classes('text-red-600 mb-4')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认删除', on_click=lambda: self.handle_delete_user(dialog, user.get('id'))).props('flat bg-red-600 text-white')

        dialog.open()

    def handle_delete_user(self, dialog, user_id: str):
        """处理删除用户"""
        if api_client.delete_user(user_id):
            dialog.close()
            self.load_users()

    def show_reset_password_dialog(self, user: Dict[str, Any]):
        """显示重置密码对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('重置密码').classes('text-xl font-bold mb-4')
            ui.label(f"为用户 '{user.get('username')}' 设置新密码").classes('mb-4')

            password_input = ui.input('新密码*', placeholder='请输入新密码', password=True, password_toggle_button=True).props('outlined')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认重置', on_click=lambda: self.handle_reset_password(dialog, user.get('id'), password_input.value)).props('flat')

        dialog.open()

    def handle_reset_password(self, dialog, user_id: str, new_password: str):
        """处理重置密码"""
        if not new_password:
            ui.notify("密码不能为空", type="warning")
            return

        if api_client.reset_user_password(user_id, new_password):
            dialog.close()


# 全局实例
users_page = UsersPage()


def show_users_page():
    """注册用户管理页面"""

    @ui.page('/admin/users')
    def page():
        # 加载数据
        users_page.load_users()

        with ui.column().classes('w-full p-4 gap-4'):
            # 标题和操作栏
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('用户管理').classes('text-2xl font-bold')

                with ui.row():
                    ui.button(icon='refresh', on_click=users_page.load_users).props('flat').tooltip('刷新')
                    ui.button('➕ 创建用户', on_click=users_page.show_create_user_dialog).props('flat')

            # 统计信息
            ui.label(f'共 {len(users_page.users_data)} 个用户').classes('text-gray-600')

            # 用户列表表格
            with ui.card().classes('w-full'):
                columns = [
                    {'name': 'username', 'label': '用户名', 'field': 'username', 'align': 'left'},
                    {'name': 'full_name', 'label': '姓名', 'field': 'full_name', 'align': 'left'},
                    {'name': 'email', 'label': '邮箱', 'field': 'email', 'align': 'left'},
                    {'name': 'roles', 'label': '角色', 'field': 'roles', 'align': 'left'},
                    {'name': 'is_active', 'label': '状态', 'field': 'is_active', 'align': 'center'},
                    {'name': 'created_at', 'label': '创建时间', 'field': 'created_at', 'align': 'center'},
                    {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'},
                ]

                def render_table():
                    rows = users_page.format_users_for_table()

                    # 添加操作列
                    for row in rows:
                        user_id = row['id']
                        user = next((u for u in users_page.users_data if u.get('id') == user_id), None)

                        actions = []
                        if user:
                            actions.append({
                                'icon': 'edit',
                                'tooltip': '编辑',
                                'onClick': lambda u=user: users_page.show_edit_user_dialog(u)
                            })
                            actions.append({
                                'icon': 'lock_reset',
                                'tooltip': '重置密码',
                                'onClick': lambda u=user: users_page.show_reset_password_dialog(u)
                            })
                            actions.append({
                                'icon': 'delete',
                                'tooltip': '删除',
                                'onClick': lambda u=user: users_page.show_delete_user_confirm(u)
                            })

                        row['actions'] = actions

                    users_page.table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='id',
                        pagination=20
                    ).classes('w-full')

                render_table()
