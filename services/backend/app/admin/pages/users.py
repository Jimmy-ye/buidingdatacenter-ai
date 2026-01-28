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
        # 缓存角色列表用于创建/编辑用户时选择
        self.all_roles: List[Dict[str, Any]] = []

    def load_roles(self):
        """加载角色列表（用于下拉选择）"""
        try:
            print("[FRONTEND] Loading roles for user form...")
            self.all_roles = api_client.get_roles()
            print(f"[FRONTEND] Loaded {len(self.all_roles)} roles for user form")
        except Exception as e:
            print(f"[FRONTEND ERROR] Failed to load roles for user form: {e}")

    def load_users(self):
        """加载用户列表"""
        try:
            print(f"[FRONTEND] Loading users... (page={self.current_page}, size={self.page_size})")
            self.users_data = api_client.get_users(
                skip=self.current_page * self.page_size,
                limit=self.page_size
            )
            print(f"[FRONTEND] Loaded {len(self.users_data)} users, type={type(self.users_data)}")
            if self.users_data:
                print(f"[FRONTEND] First user data keys: {list(self.users_data[0].keys())}")
            else:
                print("[FRONTEND] No user data returned")
            self.refresh_table()
        except Exception as e:
            print(f"[FRONTEND ERROR] Failed to load users: {e}")
            import traceback
            traceback.print_exc()

    def refresh_table(self):
        """刷新表格数据"""
        if hasattr(self, 'table'):
            self.table.props('rows-per-page-options=[20,50,100]')
            self.table.rows = self.format_users_for_table()
            self.table.update()

    def format_users_for_table(self) -> List[Dict[str, Any]]:
        """格式化用户数据用于表格显示"""
        formatted: List[Dict[str, Any]] = []
        try:
            for user in self.users_data:
                # 获取角色列表（使用 display_name 或 name）
                roles_str = ', '.join([r.get('display_name') or r.get('name', '?') for r in user.get('roles', [])])
                row = {
                    'id': user.get('id'),
                    'username': user.get('username'),
                    'full_name': user.get('full_name') or '-',
                    'email': user.get('email') or '-',
                    'roles': roles_str,
                    'is_active': '✓' if user.get('is_active') else '✗',
                    'created_at': user.get('created_at', '-')[:10] if user.get('created_at') else '-',
                }
                formatted.append(row)
            print(f"[FRONTEND] format_users_for_table produced {len(formatted)} rows")
            if formatted:
                print(f"[FRONTEND] First formatted row: {formatted[0]}")
        except Exception as e:
            print(f"[FRONTEND ERROR] format_users_for_table failed: {e}")
            import traceback
            traceback.print_exc()
        return formatted

    def show_create_user_dialog(self):
        """显示创建用户对话框"""
        # 确保角色列表已加载
        if not self.all_roles:
            self.load_roles()

        with ui.dialog() as dialog, ui.card():
            ui.label('创建新用户').classes('text-xl font-bold mb-4')

            username_input = ui.input('用户名*', placeholder='请输入用户名').props('outlined')
            full_name_input = ui.input('姓名', placeholder='请输入姓名').props('outlined')
            email_input = ui.input('邮箱', placeholder='请输入邮箱').props('outlined')
            password_input = ui.input('密码*', placeholder='请输入密码', password=True, password_toggle_button=True).props('outlined')
            phone_input = ui.input('电话', placeholder='请输入电话').props('outlined')

            # 角色选择：从后端拉取角色列表，多选下拉（value 优先使用 code，兼容 name）
            role_options = [
                {
                    'label': f"{r.get('display_name') or r.get('name')} ({r.get('code') or r.get('name')})",
                    'value': r.get('code') or r.get('name'),
                }
                for r in self.all_roles
            ]
            print(f"[FRONTEND] Role options for user form: {[o['value'] for o in role_options]}")
            role_select = ui.select(
                options=role_options,
                label='角色',
                with_input=True,
                multiple=True,
            ).props('outlined use-chips')

            with ui.row():
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('创建', on_click=lambda: self.handle_create_user(
                    dialog,
                    username_input.value,
                    full_name_input.value,
                    email_input.value,
                    password_input.value,
                    phone_input.value,
                    role_select.value,
                )).props('flat')

        dialog.open()

    def handle_create_user(self, dialog, username: str, full_name: str, email: str,
                          password: str, phone: str, role_values):
        """处理创建用户"""
        if not username or not password:
            ui.notify("用户名和密码不能为空", type="warning")
            return

        # 解析角色（多选下拉返回 list 或单值）
        if isinstance(role_values, list):
            role_codes = [v for v in role_values if v]
        elif role_values:
            role_codes = [role_values]
        else:
            role_codes = []
        print(f"[FRONTEND] Creating user with roles: {role_codes}")

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

        try:
            result = api_client.create_user(user_data)
            print(f"[FRONTEND] create_user result: {result}")
            if result and "error" not in result:
                dialog.close()
                self.load_users()
            else:
                ui.notify("创建用户失败", type="negative")
        except Exception as e:
            print(f"[FRONTEND ERROR] create_user call failed: {e}")
            import traceback
            traceback.print_exc()
            ui.notify("创建用户接口调用异常", type="negative")

    def show_edit_user_dialog(self, user: Dict[str, Any]):
        """显示编辑用户对话框"""
        with ui.dialog() as dialog, ui.card():
            ui.label('编辑用户').classes('text-xl font-bold mb-4')

            full_name_input = ui.input('姓名', value=user.get('full_name') or '').props('outlined')
            email_input = ui.input('邮箱', value=user.get('email') or '').props('outlined')
            phone_input = ui.input('电话', value=user.get('phone') or '').props('outlined')

            # 角色显示（使用 display_name 或 name）
            current_roles = ', '.join([r.get('display_name') or r.get('name', '?') for r in user.get('roles', [])])
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
        print(f"[FRONTEND] Deleting user: {user_id}")
        if api_client.delete_user(user_id):
            print("[FRONTEND] Delete user succeeded")
            dialog.close()
            self.load_users()
        else:
            print("[FRONTEND ERROR] Delete user failed")
            ui.notify("删除用户失败", type="negative")

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

        print(f"[FRONTEND] Resetting password for user: {user_id}")
        if api_client.reset_user_password(user_id, new_password):
            print("[FRONTEND] Reset password succeeded")
            dialog.close()
        else:
            print("[FRONTEND ERROR] Reset password failed")
            ui.notify("重置密码失败", type="negative")


# 全局实例
users_page = UsersPage()


def show_users_page():
    """注册用户管理页面"""

    @ui.page('/admin/users')
    def page():
        try:
            print(f"[FRONTEND] /admin/users page called")
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
                        try:
                            print(f"[FRONTEND] Rendering table with {len(users_page.users_data)} users")
                            rows = users_page.format_users_for_table()
                            print(f"[FRONTEND] Formatted {len(rows)} rows for table, sample={rows[0] if rows else 'EMPTY'}")
                            users_page.table = ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id',
                                pagination=20,
                            ).classes('w-full')

                            # 在 NiceGUI 3.x 中使用模板 slot + 自定义事件来渲染操作列
                            users_page.table.add_slot('body-cell-actions', r'''
                                <q-td :props="props">
                                    <q-btn
                                      flat round dense
                                      icon="edit"
                                      @click="$parent.$emit('user_edit', props.row.id)"
                                    />
                                    <q-btn
                                      flat round dense
                                      icon="lock_reset"
                                      @click="$parent.$emit('user_reset_password', props.row.id)"
                                    />
                                    <q-btn
                                      flat round dense
                                      color="red"
                                      icon="delete"
                                      @click="$parent.$emit('user_delete', props.row.id)"
                                    />
                                </q-td>
                            ''')

                            def _get_user_by_id(user_id: str):
                                return next((u for u in users_page.users_data if u.get('id') == user_id), None)

                            def _extract_first_arg(e):
                                """兼容不同 NiceGUI 版本下自定义事件参数结构，尽量取出第一个参数。"""
                                data = getattr(e, 'args', None)
                                # 直接是值
                                if not isinstance(data, (list, tuple, dict)):
                                    return data
                                # 列表 / 元组
                                if isinstance(data, (list, tuple)):
                                    return data[0] if data else None
                                # 可能是 {'args': [...]} 结构
                                inner = data.get('args') if isinstance(data, dict) else None
                                if isinstance(inner, (list, tuple)) and inner:
                                    return inner[0]
                                return None

                            def _on_user_edit(e):
                                user_id = _extract_first_arg(e)
                                print(f"[FRONTEND] user_edit event, user_id={user_id}, raw_args={getattr(e, 'args', None)}")
                                if not user_id:
                                    return
                                user = _get_user_by_id(user_id)
                                if user:
                                    users_page.show_edit_user_dialog(user)

                            def _on_user_reset_password(e):
                                user_id = _extract_first_arg(e)
                                print(f"[FRONTEND] user_reset_password event, user_id={user_id}, raw_args={getattr(e, 'args', None)}")
                                if not user_id:
                                    return
                                user = _get_user_by_id(user_id)
                                if user:
                                    users_page.show_reset_password_dialog(user)

                            def _on_user_delete(e):
                                user_id = _extract_first_arg(e)
                                print(f"[FRONTEND] user_delete event, user_id={user_id}, raw_args={getattr(e, 'args', None)}")
                                if not user_id:
                                    return
                                user = _get_user_by_id(user_id)
                                if user:
                                    users_page.show_delete_user_confirm(user)

                            users_page.table.on('user_edit', _on_user_edit)
                            users_page.table.on('user_reset_password', _on_user_reset_password)
                            users_page.table.on('user_delete', _on_user_delete)

                            print(f"[FRONTEND] Table created successfully with actions slot (NiceGUI 3.x)")
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
