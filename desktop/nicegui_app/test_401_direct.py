# -*- coding: utf-8 -*-
"""
直接测试 401 处理 - 调试版本

用于调试 401 自动处理机制
"""
from nicegui import ui
from desktop.nicegui_app.auth_manager import get_auth_manager
import requests


def show_401_direct_test_page():
    """显示直接 401 测试页面"""

    # 认证检查
    auth_manager = get_auth_manager()
    if not auth_manager.is_authenticated():
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    # 页面标题
    ui.label('401 直接测试（调试版）').classes('text-h4 text-center q-mb-md')
    ui.separator()

    # 测试 1: 直接调用 _handle_401
    with ui.card().classes('q-mb-md'):
        ui.label('测试 1: 直接调用 _handle_401').classes('text-subtitle1 q-mb-sm')
        ui.label('创建一个假的 401 响应对象，直接调用处理方法。').classes('text-caption q-mb-sm')

        async def test_direct_handle():
            """直接调用 _handle_401"""
            try:
                # 创建一个假的 401 响应对象
                class FakeResponse:
                    status_code = 401

                fake_response = FakeResponse()

                # 直接调用 _handle_401
                ui.notify('即将调用 _handle_401...', type='info')

                # 给一点时间让通知显示
                import asyncio
                await asyncio.sleep(1)

                result = auth_manager._handle_401(fake_response)

                ui.notify(f'_handle_401 返回: {result}', type='info')

                # 检查状态
                if not auth_manager.is_authenticated():
                    ui.notify('Token 已清除', type='positive')
                else:
                    ui.notify('Token 未清除', type='negative')

            except Exception as e:
                ui.notify(f'错误: {str(e)}', type='negative')

        ui.button('测试直接调用', on_click=test_direct_handle).props('push')

    # 测试 2: 通过 API 调用触发
    with ui.card().classes('q-mb-md'):
        ui.label('测试 2: 通过 API 触发 401').classes('text-subtitle1 q-mb-sm')
        ui.label('使用无效 token 调用 API。').classes('text-caption q-mb-sm')

        async def test_via_api():
            """通过 API 触发"""
            try:
                # 保存原始 token
                original_token = auth_manager._token

                # 设置无效 token
                auth_manager._token = "invalid"

                ui.notify('准备调用 API...', type='info')

                # 调用 API
                response = auth_manager.get('/projects/')

                ui.notify(f'API 返回状态码: {response.status_code}', type='info')

                # 恢复 token
                auth_manager._token = original_token

            except Exception as e:
                ui.notify(f'异常: {str(e)}', type='info')

        ui.button('测试 API 调用', on_click=test_via_api).props('push')

    # 测试 3: 手动登出测试
    with ui.card().classes('q-mb-md'):
        ui.label('测试 3: 手动登出').classes('text-subtitle1 q-mb-sm')
        ui.label('测试 logout() 和 navigate.to() 是否正常工作。').classes('text-caption q-mb-sm')

        async def test_manual_logout():
            """手动测试登出"""
            try:
                ui.notify('即将执行 logout()...', type='info')

                auth_manager.logout()

                ui.notify('即将跳转到登录页...', type='info')

                import asyncio
                await asyncio.sleep(1)

                ui.navigate.to('/login')

            except Exception as e:
                ui.notify(f'错误: {str(e)}', type='negative')

        ui.button('测试手动登出', on_click=test_manual_logout).props('push')

    # 当前状态
    ui.separator().classes('q-my-md')
    with ui.card().classes('q-pa-md'):
        ui.label('当前状态').classes('text-h6 q-mb-sm')

        is_auth = auth_manager.is_authenticated()
        has_token = auth_manager.token is not None
        has_user = auth_manager.user is not None

        ui.label(f'''
        认证状态: {is_auth}
        有 Token: {has_token}
        有用户信息: {has_user}
        Token 值: {auth_manager.token[:30] if auth_manager.token else 'None'}...
        ''').classes('text-body1 font-mono')

    # 返回按钮
    ui.button('返回主页', on_click=lambda: ui.navigate.to('/')).props('outline')


def register_direct_test_route():
    """注册直接测试页面路由"""

    @ui.page('/test-401-direct')
    def direct_test_page():
        """直接测试页面路由"""
        show_401_direct_test_page()


# 尝试注册
try:
    register_direct_test_route()
    print("[INFO] 401 直接测试页面已启用: http://localhost:8080/test-401-direct")
except RuntimeError:
    pass
