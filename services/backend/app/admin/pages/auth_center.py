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
                # 用户管理 Panel
                with ui.tab_panel('users'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('用户管理').classes('text-xl font-bold')
                        with ui.row():
                            ui.button(icon='refresh', on_click=users_page.load_users).props('flat').tooltip('刷新')
                            ui.button('➕ 创建用户', on_click=users_page.show_create_user_dialog).props('flat')

                    ui.label(lambda: f'共 {len(users_page.users_data)} 个用户').classes('text-gray-600')

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

                        try:
                            print('[FRONTEND] /admin/auth users tab render table')
                            rows = users_page.format_users_for_table()
                            users_table = ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id',
                                pagination=20,
                            ).classes('w-full')

                            @users_table.add_slot('body-cell-actions')
                            def _(row):
                                try:
                                    print(f"[FRONTEND] /admin/auth users actions slot row={row}")
                                    user_id = row.get('id')
                                    user = next((u for u in users_page.users_data if u.get('id') == user_id), None)
                                    if not user:
                                        print(f"[FRONTEND WARN] /admin/auth users actions: user not found for id={user_id}")
                                        return

                                    with ui.row().classes('items-center justify-center gap-1'):
                                        ui.button(
                                            icon='edit',
                                            on_click=lambda u=user: users_page.show_edit_user_dialog(u),
                                        ).props('flat round dense').tooltip('编辑')
                                        ui.button(
                                            icon='lock_reset',
                                            on_click=lambda u=user: users_page.show_reset_password_dialog(u),
                                        ).props('flat round dense').tooltip('重置密码')
                                        ui.button(
                                            icon='delete',
                                            on_click=lambda u=user: users_page.show_delete_user_confirm(u),
                                        ).props('flat round dense color=red').tooltip('删除')
                                except Exception as e:
                                    print(f"[FRONTEND ERROR] /admin/auth users actions render failed: {e}")
                        except Exception as e:
                            print(f"[FRONTEND ERROR] /admin/auth users tab render failed: {e}")

                # 角色管理 Panel
                with ui.tab_panel('roles'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('角色管理').classes('text-xl font-bold')
                        with ui.row():
                            ui.button(icon='refresh', on_click=roles_page.load_roles).props('flat').tooltip('刷新')
                            ui.button('➕ 创建角色', on_click=roles_page.show_create_role_dialog).props('flat')

                    ui.label(lambda: f'共 {len(roles_page.roles_data)} 个角色').classes('text-gray-600')

                    with ui.card().classes('w-full'):
                        columns = [
                            {'name': 'name', 'label': '角色名', 'field': 'name', 'align': 'left'},
                            {'name': 'display_name', 'label': '显示名', 'field': 'display_name', 'align': 'left'},
                            {'name': 'level', 'label': '级别', 'field': 'level', 'align': 'center'},
                            {'name': 'description', 'label': '描述', 'field': 'description', 'align': 'left'},
                            {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'},
                        ]

                        try:
                            print('[FRONTEND] /admin/auth roles tab render table')
                            rows = roles_page.format_roles_for_table()
                            roles_table = ui.table(
                                columns=columns,
                                rows=rows,
                                row_key='id',
                            ).classes('w-full')

                            @roles_table.add_slot('body-cell-actions')
                            def _(row):
                                try:
                                    print(f"[FRONTEND] /admin/auth roles actions slot row={row}")
                                    role_id = row.get('id')
                                    role = next((r for r in roles_page.roles_data if r.get('id') == role_id), None)
                                    if not role:
                                        print(f"[FRONTEND WARN] /admin/auth roles actions: role not found for id={role_id}")
                                        return

                                    with ui.row().classes('items-center justify-center gap-1'):
                                        ui.button(
                                            icon='edit',
                                            on_click=lambda r=role: roles_page.show_edit_role_dialog(r),
                                        ).props('flat round dense').tooltip('编辑')
                                        ui.button(
                                            icon='delete',
                                            on_click=lambda r=role: roles_page.show_delete_role_confirm(r),
                                        ).props('flat round dense color=red').tooltip('删除')
                                except Exception as e:
                                    print(f"[FRONTEND ERROR] /admin/auth roles actions render failed: {e}")
                        except Exception as e:
                            print(f"[FRONTEND ERROR] /admin/auth roles tab render failed: {e}")
