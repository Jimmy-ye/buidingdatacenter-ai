"""
BDC-AI 账号权限管理界面 - 主应用入口
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 从 services/backend/app/admin/main.py 向上4级到达项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from nicegui import ui
from typing import Optional
from services.backend.app.admin.services.api_client import api_client
import traceback



class AdminApp:
    """管理应用主类"""

    def __init__(self):
        self.current_user: Optional[dict] = None
        self.is_logged_in = False
        # 统计标签引用
        self.user_count_label = None
        self.role_count_label = None
        self.permission_count_label = None

    def show_login_page(self):
        """显示登录页面"""
        @ui.page('/')
        def login_page():
            with ui.card().classes('w-96 p-8'):
                ui.label('BDC-AI 账号管理').classes('text-2xl font-bold mb-6')

                username_input = ui.input('用户名', placeholder='请输入用户名')
                username_input.props('outlined')

                password_input = ui.input('密码', placeholder='请输入密码', password=True)
                password_input.props('outlined')

                async def handle_login():
                    username = username_input.value
                    password = password_input.value

                    # 去除前后空格
                    if username:
                        username = username.strip()
                    if password:
                        password = password.strip()

                    if not username or not password:
                        ui.notify("请输入用户名和密码", type="warning")
                        return

                    # 调用登录 API
                    if api_client.login(username, password):
                        self.is_logged_in = True
                        user_info = api_client.get_current_user()
                        if user_info and "error" not in user_info:
                            self.current_user = user_info
                            ui.notify(f"欢迎回来，{user_info.get('full_name', username)}！", type="positive")
                            # 跳转到主界面
                            ui.navigate.to('/admin')
                        else:
                            ui.notify("获取用户信息失败", type="negative")
                            self.is_logged_in = False

                ui.button('登录', on_click=handle_login).classes('w-full mt-4')
                ui.label('默认账号: yerui/ye123456 或 admin/admin123').classes('text-sm text-gray-500 mt-4')

    def show_admin_page(self):
        """显示管理主界面"""
        @ui.page('/admin')
        def admin_page():
            # 检查登录状态
            if not self.is_logged_in or not self.current_user:
                ui.navigate.to('/')
                return

            # 检查用户权限
            roles = self.current_user.get('roles', [])
            if not roles:
                ui.notify("您没有管理员权限", type="warning")
                return

            with ui.header().classes('bg-blue-600 text-white'):
                ui.label('BDC-AI 账号管理').classes('text-xl font-bold')
                ui.space()
                ui.label(f"当前用户: {self.current_user.get('full_name', self.current_user.get('username'))}").classes('mr-4')
                ui.button(icon='logout', on_click=self.handle_logout).props('flat round')

            with ui.left_drawer().classes('bg-blue-50'):
                ui.label('导航菜单').classes('text-lg font-bold mb-4')
                ui.button('📋 用户管理', on_click=lambda: ui.navigate.to('/admin/users')).classes('w-full justify-start').props('flat')
                ui.button('👥 角色管理', on_click=lambda: ui.navigate.to('/admin/roles')).classes('w-full justify-start').props('flat')
                ui.button('🔐 权限查看', on_click=lambda: ui.navigate.to('/admin/permissions')).classes('w-full justify-start').props('flat')
                ui.button('📝 审计日志', on_click=lambda: ui.navigate.to('/admin/audit')).classes('w-full justify-start').props('flat')

            with ui.column().classes('p-4 w-full'):
                ui.label('欢迎使用 BDC-AI 账号管理系统').classes('text-2xl font-bold mb-4')
                ui.label('请从左侧菜单选择功能').classes('text-gray-600')

                # 快速统计卡片
                with ui.row().classes('w-full gap-4'):
                    with ui.card().classes('flex-1 p-4'):
                        ui.label('用户总数').classes('text-gray-600 text-sm')
                        self.user_count_label = ui.label('-').classes('text-3xl font-bold text-blue-600')

                    with ui.card().classes('flex-1 p-4'):
                        ui.label('角色总数').classes('text-gray-600 text-sm')
                        self.role_count_label = ui.label('-').classes('text-3xl font-bold text-green-600')

                    with ui.card().classes('flex-1 p-4'):
                        ui.label('权限总数').classes('text-gray-600 text-sm')
                        self.permission_count_label = ui.label('-').classes('text-3xl font-bold text-purple-600')

                # 加载统计数据
                self.load_statistics()

    def load_statistics(self):
        """加载统计数据"""
        if not self.user_count_label or not self.role_count_label or not self.permission_count_label:
            return

        users = api_client.get_users(limit=1)
        roles = api_client.get_roles(limit=1)
        permissions = api_client.get_permissions(limit=1)

        if isinstance(users, dict):
            self.user_count_label.text = str(users.get('total', len(users)))
        elif isinstance(users, list):
            self.user_count_label.text = str(len(users))

        if isinstance(roles, dict):
            self.role_count_label.text = str(roles.get('total', len(roles)))
        elif isinstance(roles, list):
            self.role_count_label.text = str(len(roles))

        if isinstance(permissions, dict):
            self.permission_count_label.text = str(permissions.get('total', len(permissions)))
        elif isinstance(permissions, list):
            self.permission_count_label.text = str(len(permissions))

    def handle_logout(self):
        """处理登出"""
        api_client.logout()
        self.is_logged_in = False
        self.current_user = None
        ui.notify("已登出", type="info")
        ui.navigate.to('/')

    def run(self):
        """运行应用"""
        # 注册页面
        self.show_login_page()
        self.show_admin_page()

        # 导入并注册子页面
        from services.backend.app.admin.pages.users import show_users_page
        from services.backend.app.admin.pages.roles import show_roles_page
        from services.backend.app.admin.pages.permissions import show_permissions_page
        from services.backend.app.admin.pages.audit import show_audit_page

        show_users_page()
        show_roles_page()
        show_permissions_page()
        show_audit_page()


# 创建应用实例
admin_app = AdminApp()

# 注册所有页面
admin_app.run()

# 启动 NiceGUI（必须无条件调用）
ui.run(
    title="BDC-AI 账号管理",
    port=8082,
    dark=None,
    binding_refresh_interval=0.5,
)
