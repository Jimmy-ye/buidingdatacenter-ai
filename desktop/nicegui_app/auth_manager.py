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
        self._refresh_token: Optional[str] = None  # 新增：刷新 token

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

    @property
    def refresh_token(self) -> Optional[str]:
        """获取刷新 Token"""
        return self._refresh_token

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
                self._refresh_token = data.get("refresh_token")  # 新增：保存 refresh_token
                self._user = data.get("user", {"username": username})

                # 保存到持久化存储
                app.storage.user['auth_token'] = self._token
                app.storage.user['auth_refresh_token'] = self._refresh_token  # 新增
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
        self._refresh_token = None  # 新增：清除 refresh_token

        # 清除持久化存储
        if 'auth_token' in app.storage.user:
            del app.storage.user['auth_token']
        if 'auth_refresh_token' in app.storage.user:  # 新增
            del app.storage.user['auth_refresh_token']
        if 'auth_user' in app.storage.user:
            del app.storage.user['auth_user']

    def _restore_session(self) -> None:
        """从持久化存储恢复会话"""
        try:
            token = app.storage.user.get('auth_token')
            refresh_token = app.storage.user.get('auth_refresh_token')  # 新增
            user = app.storage.user.get('auth_user')

            if token and user:
                self._token = token
                self._refresh_token = refresh_token  # 新增
                self._user = user
        except RuntimeError:
            # app.storage.user 需要在 ui.run() 之后才能访问
            # 忽略此错误，稍后会通过 ui.run() 初始化
            pass

    def _do_refresh_token(self) -> bool:
        """
        尝试使用 refresh_token 获取新的 access_token

        Returns:
            bool: 刷新是否成功
        """
        if not self._refresh_token:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self._refresh_token},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token")
                # 更新 refresh_token（如果后端返回新的）
                new_refresh_token = data.get("refresh_token")
                if new_refresh_token:
                    self._refresh_token = new_refresh_token

                # 保存到持久化存储
                app.storage.user['auth_token'] = self._token
                if new_refresh_token:
                    app.storage.user['auth_refresh_token'] = self._refresh_token

                print("[INFO] Token 刷新成功")
                return True
            else:
                # refresh_token 也无效或过期
                print(f"[WARNING] Token 刷新失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"[ERROR] Token 刷新异常: {str(e)}")
            return False

    def _handle_401(self, response: requests.Response) -> bool:
        """
        处理 401 错误（增强版：先尝试刷新 Token）

        Args:
            response: HTTP 响应对象

        Returns:
            是否处理了 401 错误（是否已登出）
        """
        if response.status_code == 401:
            # 先尝试使用 refresh_token 刷新
            if self._refresh_token:
                print("[INFO] 检测到 401，尝试刷新 Token...")

                if self._do_refresh_token():
                    # Token 刷新成功，不登出，让请求可以重试
                    print("[INFO] Token 已刷新，原请求可以重试")
                    return False  # 不登出，调用方可以重试请求
                else:
                    # Token 刷新失败，执行登出
                    print("[WARNING] Token 刷新失败，执行登出")
                    self.logout()
                    ui.notify('登录已过期，请重新登录', type='warning')
                    ui.navigate.to('/login')
                    return True  # 已登出
            else:
                # 没有 refresh_token，直接登出
                print("[INFO] 没有 refresh_token，直接登出")
                self.logout()
                ui.notify('登录已过期，请重新登录', type='warning')
                ui.navigate.to('/login')
                return True  # 已登出
        return False

    def _get_headers(self) -> dict:
        """获取请求头，包含认证信息"""
        headers = {'Content-Type': 'application/json'}

        if self.is_authenticated():
            headers['Authorization'] = f'Bearer {self._token}'

        return headers

    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发起请求，并在 401 时自动刷新 Token 并重试

        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE）
            endpoint: API 端点
            **kwargs: 其他参数

        Returns:
            HTTP 响应对象
        """
        # 第一次尝试
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )

        # 如果是 401 且有 refresh_token，尝试刷新并重试
        if response.status_code == 401 and self._refresh_token:
            print(f"[INFO] 请求 {endpoint} 返回 401，尝试刷新 Token 并重试...")

            # 尝试刷新 Token
            if self._do_refresh_token():
                # Token 刷新成功，重试请求
                headers = self._get_headers()
                # 移除可能已经存在的 headers
                kwargs.pop('headers', None)

                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                print(f"[INFO] 请求 {endpoint} 重试成功")
            else:
                # Token 刷新失败，触发登出
                print(f"[WARNING] 请求 {endpoint} Token 刷新失败")
                self._handle_401(response)

        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        GET 请求（带认证和自动 Token 刷新）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.get 参数

        Returns:
            HTTP 响应对象
        """
        # 使用带重试的请求方法
        response = self._request_with_retry('GET', endpoint, **kwargs)

        # 如果仍然返回 401（刷新失败），处理登出
        if response.status_code == 401 and self.is_authenticated():
            self._handle_401(response)

        return response

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """
        POST 请求（带认证和自动 Token 刷新）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.post 参数

        Returns:
            HTTP 响应对象
        """
        response = self._request_with_retry('POST', endpoint, **kwargs)

        if response.status_code == 401 and self.is_authenticated():
            self._handle_401(response)

        return response

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """
        PUT 请求（带认证和自动 Token 刷新）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.put 参数

        Returns:
            HTTP 响应对象
        """
        response = self._request_with_retry('PUT', endpoint, **kwargs)

        if response.status_code == 401 and self.is_authenticated():
            self._handle_401(response)

        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        DELETE 请求（带认证和自动 Token 刷新）

        Args:
            endpoint: API 端点（路径）
            **kwargs: 其他 requests.delete 参数

        Returns:
            HTTP 响应对象
        """
        response = self._request_with_retry('DELETE', endpoint, **kwargs)

        if response.status_code == 401 and self.is_authenticated():
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
