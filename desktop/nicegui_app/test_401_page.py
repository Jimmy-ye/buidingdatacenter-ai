# -*- coding: utf-8 -*-
"""
401 自动处理测试页面

用于测试认证管理器的 401 错误自动处理机制
"""
from nicegui import ui
from desktop.nicegui_app.auth_manager import get_auth_manager
import requests


def show_401_test_page():
    """显示 401 测试页面"""

    # 认证检查
    auth_manager = get_auth_manager()
    if not auth_manager.is_authenticated():
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    # 页面标题
    ui.label('401 自动处理测试').classes('text-h4 text-center q-mb-md')
    ui.separator()

    # 说明
    with ui.card().classes('q-mb-md'):
        ui.label('测试说明').classes('text-h6 q-mb-sm')
        ui.label('此页面用于测试认证系统的 401 错误自动处理机制。').classes('text-body1')
        ui.label('点击下方按钮会故意触发 401 错误，验证是否能自动登出并跳转到登录页。').classes('text-body1')

    # 测试场景
    ui.label('测试场景').classes('text-h6 q-mb-md')

    # 场景 1: 使用无效 Token
    with ui.card().classes('q-mb-md'):
        ui.label('场景 1: 使用无效 Token').classes('text-subtitle1 q-mb-sm')
        ui.label('手动构造一个无效的 Token，调用受保护的 API。').classes('text-caption q-mb-sm')

        async def test_invalid_token():
            """测试无效 Token"""
            try:
                # 保存原始 token
                original_token = auth_manager.token

                # 设置无效 token
                auth_manager._token = "invalid_token_12345"

                # 尝试调用 API
                response = requests.get(
                    f"{auth_manager.base_url}/api/v1/projects/",
                    headers={"Authorization": f"Bearer {auth_manager._token}"}
                )

                # 恢复原始 token
                auth_manager._token = original_token

                if response.status_code == 401:
                    ui.notify('成功触发 401 错误，请观察是否自动跳转到登录页', type='info')
                else:
                    ui.notify(f'意外状态码: {response.status_code}', type='negative')

            except Exception as e:
                ui.notify(f'测试失败: {str(e)}', type='negative')

        ui.button('触发场景 1', on_click=test_invalid_token).props('push').classes('q-mr-sm')

    # 场景 2: 模拟 Token 过期
    with ui.card().classes('q-mb-md'):
        ui.label('场景 2: 模拟 Token 过期').classes('text-subtitle1 q-mb-sm')
        ui.label('使用过期的 Token 格式调用 API（需要后端支持）。').classes('text-caption q-mb-sm')

        async def test_expired_token():
            """测试过期 Token"""
            try:
                # 构造一个过期的 JWT token（expired signature）
                expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDk0NTkyMDAsInN1YiI6ImFkbWluIn0.signature"

                # 尝试调用 API
                response = requests.get(
                    f"{auth_manager.base_url}/api/v1/projects/",
                    headers={"Authorization": f"Bearer {expired_token}"}
                )

                if response.status_code == 401:
                    ui.notify('成功触发 401 错误，请观察是否自动跳转到登录页', type='info')
                else:
                    ui.notify(f'意外状态码: {response.status_code}', type='negative')

            except Exception as e:
                ui.notify(f'测试失败: {str(e)}', type='negative')

        ui.button('触发场景 2', on_click=test_expired_token).props('push').classes('q-mr-sm')

    # 场景 3: 无 Token 访问
    with ui.card().classes('q-mb-md'):
        ui.label('场景 3: 无 Token 访问（通过 AuthManager）').classes('text-subtitle1 q-mb-sm')
        ui.label('临时移除 Token，使用 AuthManager 调用 API。').classes('text-caption q-mb-sm')

        async def test_no_token():
            """测试无 Token 访问"""
            try:
                # 保存原始 token
                original_token = auth_manager.token

                # 临时移除 token
                auth_manager._token = None

                # 尝试调用 API（会触发 401）
                try:
                    response = auth_manager.get('/api/v1/projects/')
                except Exception as e:
                    ui.notify(f'API 调用异常（预期行为）: {str(e)}', type='info')

                # 恢复原始 token
                auth_manager._token = original_token

                ui.notify('请观察是否自动跳转到登录页', type='info')

            except Exception as e:
                ui.notify(f'测试失败: {str(e)}', type='negative')

        ui.button('触发场景 3', on_click=test_no_token).props('push').classes('q-mr-sm')

    # 当前状态显示
    ui.separator().classes('q-my-md')

    with ui.card().classes('q-pa-md'):
        ui.label('当前认证状态').classes('text-h6 q-mb-sm')

        status_text = ui.label().classes('text-body1 q-mb-md')

        def update_status():
            """更新状态显示"""
            if auth_manager.is_authenticated():
                status_text.text = f"""
                ✓ 已登录
                用户: {auth_manager.user.get('username', 'Unknown')}
                Token: {auth_manager.token[:20] if auth_manager.token else 'None'}...
                """
            else:
                status_text.text = "✗ 未登录"

        ui.button('刷新状态', on_click=update_status).props('outline')

        # 初始更新
        update_status()

    # 返回按钮
    ui.separator().classes('q-my-md')
    ui.button('返回主页', on_click=lambda: ui.navigate.to('/')).props('outline')


def register_401_test_route():
    """注册 401 测试页面路由"""

    @ui.page('/test-401')
    def test_401_page():
        """401 测试页面路由"""
        show_401_test_page()


# 自动注册（当模块被导入时）
try:
    register_401_test_route()
except RuntimeError:
    # 如果在 NiceGUI 初始化前导入，忽略错误
    # 稍后在 pc_app.py 中手动注册
    pass
