# -*- coding: utf-8 -*-
"""
Refresh Token 功能快速测试
"""
from nicegui import ui
from desktop.nicegui_app.auth_manager import get_auth_manager


def show_refresh_token_test():
    """显示 refresh_token 测试页面"""

    auth_manager = get_auth_manager()

    ui.label('Refresh Token 功能测试').classes('text-h4 text-center q-mb-md')
    ui.separator()

    # 当前状态
    with ui.card().classes('q-mb-md'):
        ui.label('当前 Token 状态').classes('text-h6 q-mb-sm')

        has_token = auth_manager.token is not None
        has_refresh = auth_manager.refresh_token is not None
        has_user = auth_manager.user is not None

        ui.label(f'''
✓ 有 Access Token: {has_token}
✓ 有 Refresh Token: {has_refresh}
✓ 有用户信息: {has_user}

Token (前50字符): {auth_manager.token[:50] if auth_manager.token else 'None'}...

Refresh Token (前50字符): {auth_manager.refresh_token[:50] if auth_manager.refresh_token else 'None'}...
        ''').classes('text-body1 font-mono')

        if has_refresh:
            ui.label('✅ Refresh Token 已保存，自动刷新功能已启用！').classes('text-positive q-mt-md')
        else:
            ui.label('❌ Refresh Token 未保存，请重新登录').classes('text-negative q-mt-md')

    # 测试说明
    ui.separator().classes('q-my-md')

    with ui.card().classes('q-pa-md'):
        ui.label('如何测试自动刷新？').classes('text-h6 q-mb-sm')

        ui.label('''
方法 1：等待 Token 过期
- Access Token 通常 15 分钟过期
- Refresh Token 通常 7 天过期
- 过期后访问任何功能，会自动刷新

方法 2：手动模拟过期（简单测试）
1. 在此页面记住当前的 Token 值
2. 手动修改 auth_manager._token 为无效值
3. 点击下面的"模拟过期"按钮
4. 应该自动刷新 Token，不需要重新登录

方法 3：查看后端日志
- 当 Token 过期时，会看到：
  [INFO] 检测到 401，尝试刷新 Token...
  [INFO] Token 刷新成功
- 如果刷新失败：
  [WARNING] Token 刷新失败，执行登出
        ''').classes('text-body1')

    # 测试按钮
    ui.separator().classes('q-my-md')

    async def test_token_status():
        """检查 Token 状态"""
        if auth_manager.is_authenticated():
            ui.notify(f'✓ 已登录\nToken: {auth_manager.token[:30]}...', type='positive', timeout=5)
        else:
            ui.notify('✗ 未登录', type='warning')

    async def simulate_expired():
        """模拟 Token 过期"""
        if not auth_manager.is_authenticated():
            ui.notify('请先登录', type='warning')
            return

        # 保存原始 token
        original_token = auth_manager.token
        original_refresh = auth_manager.refresh_token

        # 设置无效 token
        auth_manager._token = "expired_token_12345"

        ui.notify('Token 已设置为无效值，等待 5 秒后尝试刷新...', type='info', timeout=3)

        import asyncio
        await asyncio.sleep(5)

        # 尝试调用 API（应该触发自动刷新）
        try:
            response = auth_manager.get('/projects/')

            # 检查 token 是否被更新
            if auth_manager.token != "expired_token_12345":
                ui.notify('✅ Token 已自动刷新！\n新 Token: ' + auth_manager.token[:30] + '...', type='positive')
            else:
                ui.notify('❌ Token 未刷新', type='negative')
        except Exception as e:
            ui.notify(f'错误: {str(e)}', type='negative')

    with ui.row().classes('q-gutter-sm'):
        ui.button('检查 Token 状态', on_click=test_token_status).props('outline')
        ui.button('模拟 Token 过期', on_click=simulate_expired).props('push')
        ui.button('返回主页', on_click=lambda: ui.navigate.to('/')).props('flat')


def register_refresh_test_route():
    """注册 refresh_token 测试路由"""

    @ui.page('/test-refresh')
    def refresh_test_page():
        """refresh_token 测试页面"""
        if not get_auth_manager().is_authenticated():
            ui.notify('请先登录', type='warning')
            ui.navigate.to('/login')
            return

        show_refresh_token_test()


# 尝试注册
try:
    register_refresh_test_route()
    print("[INFO] Refresh Token 测试页面已启用: http://localhost:8080/test-refresh")
except RuntimeError:
    pass
