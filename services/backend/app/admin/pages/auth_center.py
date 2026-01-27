"""
账号综合管理页面：在一个界面里同时管理用户和角色（通过 Tab 切换）
"""

from nicegui import ui
from services.backend.app.admin.pages.users import users_page
from services.backend.app.admin.pages.roles import roles_page


def show_auth_center_page():
    """注册账号综合管理页面 /admin/auth"""

    @ui.page('/admin/auth')
    def page():
        # 预加载数据
        try:
            print('[FRONTEND] /admin/auth page called')
            users_page.load_users()
            roles_page.load_roles()
            roles_page.load_permissions()
        except Exception as e:
            print(f'[FRONTEND ERROR] /admin/auth preload failed: {e}')

        with ui.column().classes('w-full p-4 gap-4'):
            ui.label('账号综合管理').classes('text-2xl font-bold')

            tabs = ui.tabs().classes('w-full')
            with tabs:
                ui.tab('users', label='用户管理')
                ui.tab('roles', label='角色管理')

            with ui.tab_panels(tabs, value='users').classes('w-full'):
                # 用户管理 Panel（只读列表，避免在此页引入 Slot 函数）
                with ui.tab_panel('users'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('用户管理').classes('text-xl font-bold')
                        with ui.row():
                            ui.button(icon='refresh', on_click=users_page.load_users).props('flat').tooltip('刷新列表')
                            ui.button('➕ 创建用户', on_click=users_page.show_create_user_dialog).props('flat')

                    # 注意：这里不要使用 ui.label(lambda: ...) 以免函数进入 JSON 序列化
                    ui.label(f'共 {len(users_page.users_data)} 个用户').classes('text-gray-600')

                    with ui.card().classes('w-full'):
                        columns = [
                            {'name': 'username', 'label': '用户名', 'field': 'username', 'align': 'left'},
                            {'name': 'full_name', 'label': '姓名', 'field': 'full_name', 'align': 'left'},
                            {'name': 'email', 'label': '邮箱', 'field': 'email', 'align': 'left'},
                            {'name': 'roles', 'label': '角色', 'field': 'roles', 'align': 'left'},
                            {'name': 'is_active', 'label': '状态', 'field': 'is_active', 'align': 'center'},
                            {'name': 'created_at', 'label': '创建时间', 'field': 'created_at', 'align': 'center'},
                        ]

                        try:
                            print('[FRONTEND] /admin/auth users tab render table (read-only)')
                            rows = users_page.format_users_for_table()
                            ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id',
                                pagination=20,
                            ).classes('w-full')
                        except Exception as e:
                            print(f"[FRONTEND ERROR] /admin/auth users tab render failed: {e}")

                # 角色管理 Panel（只读列表）
                with ui.tab_panel('roles'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('角色管理').classes('text-xl font-bold')
                        with ui.row():
                            ui.button(icon='refresh', on_click=roles_page.load_roles).props('flat').tooltip('刷新列表')
                            ui.button('➕ 创建角色', on_click=roles_page.show_create_role_dialog).props('flat')

                    # 同理，这里也使用一次性字符串而非 lambda
                    ui.label(f'共 {len(roles_page.roles_data)} 个角色').classes('text-gray-600')

                    with ui.card().classes('w-full'):
                        columns = [
                            {'name': 'name', 'label': '角色名', 'field': 'name', 'align': 'left'},
                            {'name': 'display_name', 'label': '显示名', 'field': 'display_name', 'align': 'left'},
                            {'name': 'level', 'label': '级别', 'field': 'level', 'align': 'center'},
                            {'name': 'description', 'label': '描述', 'field': 'description', 'align': 'left'},
                        ]

                        try:
                            print('[FRONTEND] /admin/auth roles tab render table (read-only)')
                            rows = roles_page.format_roles_for_table()
                            ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id',
                            ).classes('w-full')
                        except Exception as e:
                            print(f"[FRONTEND ERROR] /admin/auth roles tab render failed: {e}")
