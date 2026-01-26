"""
PC-UI 认证管理器

提供登录、登出、Token 管理和自动 401 处理
"""
import requests
from typing import Optional, Dict, Any
from nicegui import app, ui


class AuthManager:
    """认证管理器"""

    def __init__(self, base_url: str = None):
        """
        初始化认证管理器

        Args:
            base_url: 后端 API 基础 URL
        """
        from desktop.nicegui_app.config import Config

        if base_url is None:
            base_url = Config.get_api_base_url()

        self.base_url = base_url
        self._user: Optional[Dict[str, Any]] = None
        self._token: Optional[str] = None

        # 从持久化存储恢复会话
        self._restore_session()

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """获取当前用户信息"""
        return self._user

    @property
    def token(self) -> Optional[str]:
        """获取当前 Token"""
        return self._token

    def is_authenticated(self) -> bool:
        """是否已登录"""
        return self._user is not None and self._token is not None

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """
        登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (成功标志, 消息)
        """
        # 输入验证
        if not username or not password:
            return False, "用户名和密码不能为空"

        try:
            # 调用后端登录 API
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token")
                self._user = data.get("user", {"username": username})

                # 保存到持久化存储
                app.storage.user['auth_token'] = self._token
                app.storage.user['auth_user'] = self._user

                return True, "登录成功"
            elif response.status_code == 401:
                return False, "用户名或密码错误"
            else:
                return False, f"登录失败: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {str(e)}"

    def logout(self) -> None:
        """登出"""
        self._user = None
        self._token = None

        # 清除持久化存储
        if 'auth_token' in app.storage.user:
            del app.storage.user['auth_token']
        if 'auth_user' in app.storage.user:
            del app.storage.user['auth_user']

    def _restore_session(self) -> None:
        """从持久化存储恢复会话"""
        try:
            token = app.storage.user.get('auth_token')
            user = app.storage.user.get('auth_user')

            if token and user:
                self._token = token
                self._user = user
        except RuntimeError:
            # app.storage.user 需要在 ui.run() 之后才能访问
            # 忽略此错误，稍后会通过 ui.run() 初始化
            pass

    def _handle_401(self, response: requests.Response) -> bool:
        """
        处理 401 错误

        Args:
            response: HTTP 响应对象

        Returns:
            是否处理了 401 错误
        """
        if response.status_code == 401:
            # 自动登出
            self.logout()

            # 跳转到登录页
            ui.notify('登录已过期，请重新登录', type='warning')
            ui.navigate.to('/login')
            return True
        return False

    def _get_headers(self) -> dict:
        """获取请求头，包含认证信息"""
        headers = {'Content-Type': 'application/json'}

        if self.is_authenticated():
            headers['Authorization'] = f'Bearer {self._token}'

        return headers

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        GET 请求（带认证）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.get 参数

        Returns:
            HTTP 响应对象
        """
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # 处理 401
        if self.is_authenticated():
            self._handle_401(response)

        return response

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """
        POST 请求（带认证）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.post 参数

        Returns:
            HTTP 响应对象
        """
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # 处理 401
        if self.is_authenticated():
            self._handle_401(response)

        return response

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """
        PUT 请求（带认证）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.put 参数

        Returns:
            HTTP 响应对象
        """
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        response = requests.put(
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # 处理 401
        if self.is_authenticated():
            self._handle_401(response)

        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        DELETE 请求（带认证）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.delete 参数

        Returns:
            HTTP 响应对象
        """
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        response = requests.delete(
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # 处理 401
        if self.is_authenticated():
            self._handle_401(response)

        return response


# 创建全局单例（使用模块级变量）
_auth_manager_instance: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """获取全局认证管理器单例"""
    global _auth_manager_instance
    if _auth_manager_instance is None:
        _auth_manager_instance = AuthManager()
    return _auth_manager_instance


# 便捷访问函数
auth_manager = get_auth_manager()
