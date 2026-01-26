"""
PC-UI 登录页面

提供用户友好的登录界面
"""
from nicegui import ui
from desktop.nicegui_app.config import Config

# 延迟导入认证管理器，使用单例模式
_auth_manager_instance = None

def get_auth_manager():
    """延迟导入认证管理器（单例）"""
    global _auth_manager_instance
    if _auth_manager_instance is None:
        from desktop.nicegui_app.auth_manager import auth_manager
        _auth_manager_instance = auth_manager
    return _auth_manager_instance


def show_login_page():
    """显示登录页面"""

    # 判断环境
    is_dev = Config.is_development()

    # 创建居中布局
    with ui.column().classes('w-full h-full items-center justify-center'):
        with ui.card().classes('w-96 p-8'):
            # Logo 和标题
            ui.label('BDC-AI 建筑节能管理平台').classes('text-h5 text-center q-mb-md')

            # 环境标识
            if is_dev:
                ui.label('开发环境').classes('text-caption text-center text-grey q-mb-sm')
            else:
                ui.label('生产环境').classes('text-caption text-center text-blue q-mb-sm')

            ui.separator().classes('q-mb-md')

            # 错误消息显示区域
            error_label = ui.label('').classes('text-negative q-mb-sm text-center')
            error_label.visible = False

            # 用户名输入框
            username_input = ui.input(
                label='用户名',
                placeholder='请输入用户名',
                value=''
            ).props('outlined clearable').classes('q-mb-sm w-full')

            # 密码输入框
            password_input = ui.input(
                label='密码',
                placeholder='请输入密码',
                value='',
                password=True
            ).props('outlined clearable').classes('q-mb-md w-full')

            # 登录按钮
            def on_login_click():
                """登录按钮点击事件"""
                username = username_input.value or ''
                password = password_input.value or ''

                print(f"[DEBUG] 尝试登录 - 用户名: {username}")

                # 输入验证
                if not username or not password:
                    error_label.text = '用户名和密码不能为空'
                    error_label.visible = True
                    return

                # 调用认证管理器登录
                success, message = get_auth_manager().login(username, password)

                print(f"[DEBUG] 登录结果 - 成功: {success}, 消息: {message}")

                if success:
                    # 登录成功：显示通知 + 跳转主页
                    ui.notify('登录成功', type='positive')
                    ui.navigate.to('/')
                else:
                    # 登录失败：显示错误消息
                    error_label.text = message
                    error_label.visible = True

            login_button = ui.button('登录', on_click=on_login_click).props('push').classes('q-mb-md w-full')

            # 开发环境提示
            if is_dev:
                ui.separator().classes('q-mb-md')
                ui.label('提示：开发环境可使用 admin/admin123').classes('text-caption text-grey text-center')
            else:
                # 生产环境：完全不显示默认账号提示
                pass

            # 快捷键支持（Enter 键登录）
            password_input.on('keydown.enter', lambda: on_login_click())

            # 自动聚焦到用户名输入框
            username_input.run_method('focus')
