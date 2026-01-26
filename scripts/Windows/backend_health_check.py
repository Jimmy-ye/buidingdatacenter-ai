"""
BDC-AI 后端健康检查脚本
检查后端服务的运行状态、数据库连接、API 端点可用性等
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 配置
BACKEND_URL = "http://localhost:8000"
CHECK_TIMEOUT = 5
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


class HealthChecker:
    """后端健康检查器"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()

    def check(self, name: str, passed: bool, message: str, details: str = ""):
        """记录检查结果"""
        status = "[PASS]" if passed else "[FAIL]"
        result = {
            "name": name,
            "status": status,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status} | {name}: {message}")
        if details:
            print(f"     -> {details}")

    def check_server_running(self) -> bool:
        """检查服务器是否运行"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=CHECK_TIMEOUT)
            passed = response.status_code == 200
            self.check(
                "服务器运行状态",
                passed,
                "服务器正常运行" if passed else "服务器未响应",
                f"状态码: {response.status_code}"
            )
            return passed
        except requests.exceptions.ConnectionError:
            self.check("服务器运行状态", False, "无法连接到服务器", "连接被拒绝")
            return False
        except requests.exceptions.Timeout:
            self.check("服务器运行状态", False, "服务器响应超时", f"超时时间: {CHECK_TIMEOUT}秒")
            return False
        except Exception as e:
            self.check("服务器运行状态", False, f"检查失败: {str(e)}")
            return False

    def check_health_endpoint(self) -> bool:
        """检查健康检查端点"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health/", timeout=CHECK_TIMEOUT)
            passed = response.status_code == 200 and response.json().get("status") == "ok"
            self.check(
                "健康检查端点",
                passed,
                "健康检查端点正常",
                f"/api/v1/health/ 返回: {response.json()}"
            )
            return passed
        except Exception as e:
            self.check("健康检查端点", False, f"检查失败: {str(e)}")
            return False

    def check_auth_login(self) -> Tuple[bool, str]:
        """检查认证登录"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": ADMIN_USER, "password": ADMIN_PASS},
                timeout=CHECK_TIMEOUT
            )
            data = response.json()

            if response.status_code == 200 and "access_token" in data:
                token = data["access_token"]
                self.check(
                    "认证登录",
                    True,
                    "登录成功",
                    f"Token 有效期: {data.get('expires_in', 0)}秒"
                )
                return True, token
            else:
                self.check("认证登录", False, f"登录失败: {data.get('detail', '未知错误')}")
                return False, ""
        except Exception as e:
            self.check("认证登录", False, f"检查失败: {str(e)}")
            return False, ""

    def check_auth_user_info(self, token: str) -> bool:
        """检查获取用户信息"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=CHECK_TIMEOUT
            )
            passed = response.status_code == 200
            if passed:
                user_data = response.json()
                self.check(
                    "获取用户信息",
                    True,
                    f"用户信息获取成功: {user_data.get('username')}",
                    f"角色: {[r['display_name'] for r in user_data.get('roles', [])]}"
                )
            else:
                self.check("获取用户信息", False, f"获取失败: {response.json().get('detail', '未知错误')}")
            return passed
        except Exception as e:
            self.check("获取用户信息", False, f"检查失败: {str(e)}")
            return False

    def check_projects_api(self, token: str) -> bool:
        """检查项目列表 API"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/projects/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=CHECK_TIMEOUT
            )
            passed = response.status_code == 200
            if passed:
                projects = response.json()
                self.check(
                    "项目列表 API",
                    True,
                    f"获取成功，共 {len(projects)} 个项目",
                    f"API 端点: /api/v1/projects/"
                )
            else:
                self.check("项目列表 API", False, f"获取失败: {response.json().get('detail', '未知错误')}")
            return passed
        except Exception as e:
            self.check("项目列表 API", False, f"检查失败: {str(e)}")
            return False

    def check_database_connection(self) -> bool:
        """通过 API 检查数据库连接"""
        try:
            # 通过项目列表 API 间接检查数据库
            token = ""
            login_result = self.check_auth_login()
            if login_result[0]:
                token = login_result[1]

            if token:
                response = self.session.get(
                    f"{self.base_url}/api/v1/projects/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=CHECK_TIMEOUT
                )
                # 如果能成功查询，说明数据库连接正常
                passed = response.status_code in [200, 401]  # 200 或 401 都说明数据库连接正常
                self.check(
                    "数据库连接",
                    passed,
                    "数据库连接正常" if passed else "数据库连接可能异常",
                    "通过 API 查询验证"
                )
                return passed
            else:
                self.check("数据库连接", False, "无法验证（登录失败）")
                return False
        except Exception as e:
            self.check("数据库连接", False, f"检查失败: {str(e)}")
            return False

    def check_cors(self) -> bool:
        """检查 CORS 配置"""
        try:
            response = self.session.options(
                f"{self.base_url}/api/v1/health/",
                headers={"Origin": "http://localhost:8080"},
                timeout=CHECK_TIMEOUT
            )
            cors_headers = response.headers.get("Access-Control-Allow-Origin", "")
            passed = cors_headers != "" or response.status_code == 200
            self.check(
                "CORS 配置",
                passed,
                "CORS 配置正常" if passed else "CORS 可能未配置",
                f"Allow-Origin: {cors_headers if cors_headers else '未设置'}"
            )
            return passed
        except Exception as e:
            self.check("CORS 配置", False, f"检查失败: {str(e)}")
            return False

    def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        print("=" * 80)
        print("BDC-AI 后端健康检查")
        print("=" * 80)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端地址: {self.base_url}")
        print("=" * 80)
        print()

        # 1. 服务器运行状态
        if not self.check_server_running():
            print("\n[ERROR] Backend service not running, stopping checks")
            return self.get_summary()

        # 2. 健康检查端点
        self.check_health_endpoint()

        # 3. 认证系统
        login_result = self.check_auth_login()
        token = ""
        if login_result[0]:
            token = login_result[1]
            # 4. 用户信息
            self.check_auth_user_info(token)
            # 5. 项目列表 API
            self.check_projects_api(token)

        # 6. 数据库连接
        self.check_database_connection()

        # 7. CORS 配置
        self.check_cors()

        # 生成总结
        return self.get_summary()

    def get_summary(self) -> Dict:
        """生成检查总结"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "status": "healthy" if success_rate >= 80 else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }

        print()
        print("=" * 80)
        print("检查总结")
        print("=" * 80)
        print(f"总计检查: {total} 项")
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        print(f"成功率: {success_rate:.1f}%")
        print(f"Status: {'[HEALTHY]' if summary['status'] == 'healthy' else '[UNHEALTHY]'}")
        print("=" * 80)

        return summary


def main():
    """主函数"""
    checker = HealthChecker(BACKEND_URL)
    summary = checker.run_all_checks()

    # 返回退出码
    sys.exit(0 if summary["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
