"""
API 客户端 - 封装与后端的通信
"""

import requests
from typing import Optional, Dict, List, Any
from nicegui import ui


class APIClient:
    """后端 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（包含 Token）"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应，统一错误处理"""
        print(f"\n[API RESPONSE] URL: {response.url}")
        print(f"[API RESPONSE] Status: {response.status_code}")
        print(f"[API RESPONSE] Content-Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 401:
            ui.notify("登录已过期，请重新登录", type="warning")
            return {"error": "unauthorized"}

        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", str(error_data))
                print(f"[API ERROR] Detail: {message}")
                print(f"[API ERROR] Full error: {error_data}")
            except:
                message = response.text or f"HTTP {response.status_code}"
                print(f"[API ERROR] Text: {message}")
            ui.notify(f"请求失败: {message}", type="negative")
            return {"error": message}

        try:
            data = response.json()
            print(f"[API SUCCESS] Data keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return data
        except Exception as e:
            print(f"[API ERROR] JSON decode failed: {e}")
            print(f"[API ERROR] Response text: {response.text[:500]}")
            return {"error": f"Invalid JSON response: {str(e)}"}

    # ================= 认证 API =================

    def login(self, username: str, password: str) -> bool:
        """用户登录"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                print(f"[LOGIN SUCCESS] User: {username}")
                return True
            else:
                print(f"[LOGIN FAILED] User: {username}, Status: {response.status_code}")
                print(f"[LOGIN FAILED] Response: {response.text[:200]}")
                ui.notify("登录失败，请检查用户名和密码", type="negative")
                return False

        except Exception as e:
            print(f"[LOGIN ERROR] Exception: {str(e)}")
            ui.notify(f"登录错误: {str(e)}", type="negative")
            return False

    def refresh_access_token(self) -> bool:
        """刷新访问令牌"""
        if not self.refresh_token:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                return True
            else:
                return False

        except Exception:
            return False

    def logout(self) -> bool:
        """用户登出"""
        try:
            requests.post(
                f"{self.base_url}/api/v1/auth/logout",
                json={"refresh_token": self.refresh_token},
                headers=self._get_headers(),
                timeout=10
            )
        except Exception:
            pass
        finally:
            self.access_token = None
            self.refresh_token = None
        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """获取当前用户信息"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            ui.notify(f"获取用户信息失败: {str(e)}", type="negative")
            return None

    # ================= 用户管理 API =================

    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/users",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit},
                timeout=10
            )
            data = self._handle_response(response)
            return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            ui.notify(f"获取用户列表失败: {str(e)}", type="negative")
            return []

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户详情"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/users/{user_id}",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            ui.notify(f"获取用户详情失败: {str(e)}", type="negative")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建用户"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/users",
                json=user_data,
                headers=self._get_headers(),
                timeout=10
            )
            result = self._handle_response(response)
            if "error" not in result:
                ui.notify("用户创建成功", type="positive")
            return result
        except Exception as e:
            ui.notify(f"创建用户失败: {str(e)}", type="negative")
            return None

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """更新用户"""
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/auth/users/{user_id}",
                json=user_data,
                headers=self._get_headers(),
                timeout=10
            )
            result = self._handle_response(response)
            if "error" not in result:
                ui.notify("用户更新成功", type="positive")
                return True
            return False
        except Exception as e:
            ui.notify(f"更新用户失败: {str(e)}", type="negative")
            return False

    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/auth/users/{user_id}",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 204:
                ui.notify("用户删除成功", type="positive")
                return True
            else:
                self._handle_response(response)
                return False
        except Exception as e:
            ui.notify(f"删除用户失败: {str(e)}", type="negative")
            return False

    def reset_user_password(self, user_id: str, new_password: str) -> bool:
        """重置用户密码"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/users/{user_id}/reset-password",
                json={"new_password": new_password},
                headers=self._get_headers(),
                timeout=10
            )
            result = self._handle_response(response)
            if "error" not in result:
                ui.notify("密码重置成功", type="positive")
                return True
            return False
        except Exception as e:
            ui.notify(f"重置密码失败: {str(e)}", type="negative")
            return False

    # ================= 角色管理 API =================

    def get_roles(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取角色列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/roles",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit},
                timeout=10
            )
            data = self._handle_response(response)
            return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            ui.notify(f"获取角色列表失败: {str(e)}", type="negative")
            return []

    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """获取角色详情"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/roles/{role_id}",
                headers=self._get_headers(),
                timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            ui.notify(f"获取角色详情失败: {str(e)}", type="negative")
            return None

    def create_role(self, role_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建角色"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/roles",
                json=role_data,
                headers=self._get_headers(),
                timeout=10
            )
            result = self._handle_response(response)
            if "error" not in result:
                ui.notify("角色创建成功", type="positive")
            return result
        except Exception as e:
            ui.notify(f"创建角色失败: {str(e)}", type="negative")
            return None

    def update_role(self, role_id: str, role_data: Dict[str, Any]) -> bool:
        """更新角色"""
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/auth/roles/{role_id}",
                json=role_data,
                headers=self._get_headers(),
                timeout=10
            )
            result = self._handle_response(response)
            if "error" not in result:
                ui.notify("角色更新成功", type="positive")
                return True
            return False
        except Exception as e:
            ui.notify(f"更新角色失败: {str(e)}", type="negative")
            return False

    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/auth/roles/{role_id}",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 204:
                ui.notify("角色删除成功", type="positive")
                return True
            else:
                self._handle_response(response)
                return False
        except Exception as e:
            ui.notify(f"删除角色失败: {str(e)}", type="negative")
            return False

    # ================= 权限管理 API =================

    def get_permissions(self, skip: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取权限列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/permissions",
                headers=self._get_headers(),
                params={"skip": skip, "limit": limit},
                timeout=10
            )
            data = self._handle_response(response)
            return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            ui.notify(f"获取权限列表失败: {str(e)}", type="negative")
            return []

    # ================= 审计日志 API =================

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        try:
            params = {"skip": skip, "limit": limit}
            if user_id:
                params["user_id"] = user_id

            response = requests.get(
                f"{self.base_url}/api/v1/auth/audit-logs",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            data = self._handle_response(response)
            return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            ui.notify(f"获取审计日志失败: {str(e)}", type="negative")
            return []


# 全局 API 客户端实例
api_client = APIClient()
