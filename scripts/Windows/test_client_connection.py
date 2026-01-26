"""
客户端连接测试脚本
用于测试后端服务的连接可用性和 API 功能
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"  # 或 "http://100.93.101.76:8000" (Tailscale)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
TIMEOUT = 5


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

    @staticmethod
    def green(text):
        return f"{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def red(text):
        return f"{Colors.RED}{text}{Colors.RESET}"

    @staticmethod
    def yellow(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def blue(text):
        return f"{Colors.BLUE}{text}{Colors.RESET}"


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 70)
    print(Colors.blue(text))
    print("=" * 70)


def print_success(text):
    """打印成功信息"""
    print(f"[{Colors.green('PASS')}] {text}")


def print_error(text):
    """打印错误信息"""
    print(f"[{Colors.red('FAIL')}] {text}")


def print_info(text):
    """打印信息"""
    print(f"[{Colors.yellow('INFO')}] {text}")


def test_basic_connection():
    """测试基础连接"""
    print_header("1. 基础连接测试")
    print(f"后端地址: {BACKEND_URL}")

    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("基础连接正常")
            print_info(f"响应: {response.json()}")
            return True
        else:
            print_error(f"状态码异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("连接被拒绝，请确认后端服务是否启动")
        return False
    except requests.exceptions.Timeout:
        print_error("连接超时")
        return False
    except Exception as e:
        print_error(f"连接失败: {e}")
        return False


def test_health_check():
    """测试健康检查端点"""
    print_header("2. 健康检查端点")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health/", timeout=TIMEOUT)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "ok":
            print_success("健康检查正常")
            print_info(f"响应: {data}")
            return True
        else:
            print_error("健康检查失败")
            return False
    except Exception as e:
        print_error(f"健康检查异常: {e}")
        return False


def test_login():
    """测试登录"""
    print_header("3. 用户登录测试")
    print(f"用户名: {ADMIN_USER}")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()

            if "access_token" in data and "refresh_token" in data:
                print_success("登录成功")
                print_info(f"Token 类型: {data.get('token_type')}")
                print_info(f"有效期: {data.get('expires_in')} 秒")
                return True, data["access_token"]
            else:
                print_error("Token 缺失")
                return False, None
        else:
            data = response.json()
            print_error(f"登录失败: {data.get('detail', '未知错误')}")
            return False, None

    except Exception as e:
        print_error(f"登录异常: {e}")
        return False, None


def test_user_info(token):
    """测试获取用户信息"""
    print_header("4. 用户信息查询")

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            print_success("用户信息获取成功")
            print_info(f"用户名: {data.get('username')}")
            print_info(f"邮箱: {data.get('email')}")
            print_info(f"全名: {data.get('full_name')}")
            print_info(f"角色: {', '.join([r['display_name'] for r in data.get('roles', [])])}")
            return True
        else:
            print_error(f"获取失败: {response.json().get('detail', '未知错误')}")
            return False

    except Exception as e:
        print_error(f"查询异常: {e}")
        return False


def test_projects_api(token):
    """测试项目 API"""
    print_header("5. 项目列表 API")

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/projects/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            projects = response.json()
            print_success("项目列表获取成功")
            print_info(f"项目数量: {len(projects)}")

            if projects:
                print_info("前 3 个项目:")
                for i, project in enumerate(projects[:3], 1):
                    print_info(f"  {i}. {project.get('name')} (ID: {project.get('id')})")
            return True
        else:
            print_error(f"获取失败: {response.json().get('detail', '未知错误')}")
            return False

    except Exception as e:
        print_error(f"查询异常: {e}")
        return False


def test_cors():
    """测试 CORS"""
    print_header("6. CORS 配置测试")

    try:
        response = requests.options(
            f"{BACKEND_URL}/api/v1/health/",
            headers={"Origin": "http://localhost:8080"},
            timeout=TIMEOUT
        )

        cors_headers = response.headers.get("Access-Control-Allow-Origin", "")

        if cors_headers:
            print_success("CORS 已配置")
            print_info(f"Access-Control-Allow-Origin: {cors_headers}")
            return True
        else:
            print_error("CORS 未配置或配置不正确")
            return False

    except Exception as e:
        print_error(f"CORS 检查异常: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("BDC-AI 客户端连接测试")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BACKEND_URL}")
    print("=" * 70)

    results = []

    # 1. 基础连接
    result = test_basic_connection()
    results.append(("基础连接", result))
    if not result:
        print("\n" + Colors.red("后端服务未运行，停止测试"))
        return False

    # 2. 健康检查
    result = test_health_check()
    results.append(("健康检查", result))

    # 3. 登录
    login_result, token = test_login()
    results.append(("用户登录", login_result))

    if token:
        # 4. 用户信息
        result = test_user_info(token)
        results.append(("用户信息", result))

        # 5. 项目 API
        result = test_projects_api(token)
        results.append(("项目 API", result))

    # 6. CORS
    result = test_cors()
    results.append(("CORS 配置", result))

    # 打印总结
    print_header("测试总结")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"总计测试: {total} 项")
    print(f"通过: {Colors.green(str(passed))} 项")
    print(f"失败: {Colors.red(str(failed))} 项")
    print(f"成功率: {success_rate:.1f}%")
    print()

    print("详细结果:")
    for name, result in results:
        status = Colors.green("PASS") if result else Colors.red("FAIL")
        print(f"  [{status}] {name}")

    print("\n" + "=" * 70)

    if success_rate >= 80:
        print(Colors.green("✓ 后端服务状态良好，可以接受客户端连接"))
        return True
    else:
        print(Colors.red("✗ 后端服务存在问题，需要修复"))
        return False


def main():
    """主函数"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
