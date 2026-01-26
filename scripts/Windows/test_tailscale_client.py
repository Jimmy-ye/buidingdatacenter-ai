"""
客户端 Tailscale 连接测试脚本
在客户端机器上运行，测试能否连接到后端服务器
"""

import requests
import socket
import sys
from datetime import datetime

# 后端 Tailscale IP
BACKEND_IP = "100.93.101.76"
BACKEND_URL = f"http://{BACKEND_IP}:8000"


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text):
    print(f"[OK] {text}")


def print_error(text):
    print(f"[FAIL] {text}")


def print_info(text):
    print(f"[INFO] {text}")


def test_tcp_connection():
    """测试 1: TCP 端口连接"""
    print_header("测试 1: TCP 端口连接 (8000)")

    print_info(f"目标: {BACKEND_IP}:8000")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((BACKEND_IP, 8000))
        sock.close()

        if result == 0:
            print_success(f"TCP 端口 8000 连接成功")
            return True
        else:
            print_error(f"TCP 端口 8000 无法连接")
            return False

    except Exception as e:
        print_error(f"TCP 连接失败: {e}")
        return False


def test_http_connection():
    """测试 2: HTTP 连接"""
    print_header("测试 2: HTTP 连接")

    print_info(f"URL: {BACKEND_URL}/")

    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("HTTP 连接成功")
            print_info(f"响应: {data}")
            return True
        else:
            print_error(f"HTTP 错误: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("无法建立 HTTP 连接")
        print_info("可能的原因:")
        print_info("  1. 后端服务未启动")
        print_info("  2. 后端未监听 0.0.0.0（只监听 127.0.0.1）")
        print_info("  3. 防火墙阻止连接")
        return False
    except requests.exceptions.Timeout:
        print_error("连接超时（10秒）")
        return False
    except Exception as e:
        print_error(f"HTTP 测试失败: {e}")
        return False


def test_health_check():
    """测试 3: 健康检查端点"""
    print_header("测试 3: 健康检查端点")

    print_info(f"URL: {BACKEND_URL}/api/v1/health/")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health/", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("健康检查端点正常")
            print_info(f"状态: {data.get('status')}")
            return True
        else:
            print_error(f"健康检查失败: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"健康检查测试失败: {e}")
        return False


def test_login():
    """测试 4: 用户登录"""
    print_header("测试 4: 用户登录")

    print_info("使用管理员账号登录...")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success("登录成功")
            print_info(f"Token 类型: {data.get('token_type')}")
            print_info(f"有效期: {data.get('expires_in')} 秒")

            if data.get('access_token'):
                print_success("Access Token 获取成功")
                return True
        else:
            error_detail = response.json().get('detail', '未知错误')
            print_error(f"登录失败: {error_detail}")
            return False

    except Exception as e:
        print_error(f"登录测试失败: {e}")
        return False


def test_api_docs():
    """测试 5: API 文档访问"""
    print_header("测试 5: API 文档")

    print_info(f"URL: {BACKEND_URL}/docs")

    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)

        if response.status_code == 200:
            print_success("API 文档可访问")
            print_info("可以在浏览器中打开查看完整 API 文档")
            print_info(f"  浏览器地址: {BACKEND_URL}/docs")
            return True
        else:
            print_error(f"API 文档返回: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"API 文档测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("客户端 Tailscale 连接测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BACKEND_URL}")
    print()

    results = []

    # 测试 1: TCP 连接
    result = test_tcp_connection()
    results.append(("TCP 端口连接", result))

    if not result:
        print("\n" + "=" * 60)
        print("[ERROR] TCP 端口无法连接，停止测试")
        print("=" * 60)
        print("\n请检查:")
        print("  1. 后端服务是否启动")
        print("  2. 后端监听地址是否为 0.0.0.0")
        print("  3. 防火墙设置")
        return False

    # 测试 2: HTTP 连接
    result = test_http_connection()
    results.append(("HTTP 连接", result))

    if not result:
        print("\n" + "=" * 60)
        print("[ERROR] HTTP 无法连接，停止测试")
        print("=" * 60)
        return False

    # 测试 3: 健康检查
    result = test_health_check()
    results.append(("健康检查", result))

    # 测试 4: 登录
    result = test_login()
    results.append(("用户登录", result))

    # 测试 5: API 文档
    result = test_api_docs()
    results.append(("API 文档", result))

    # 打印总结
    print_header("测试总结")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    failed = total - failed

    print(f"总计测试: {total} 项")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print()

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print()
    print("=" * 60)

    if passed == total:
        print("[SUCCESS] 客户端可以正常连接后端！")
        print()
        print("连接信息:")
        print(f"  后端地址: {BACKEND_URL}")
        print(f"  API 文档: {BACKEND_URL}/docs")
        print(f"  健康检查: {BACKEND_URL}/api/v1/health/")
        print()
        print("你现在可以在客户端使用后端服务了！")
        print("=" * 60)
        return True
    else:
        print("[WARNING] 部分测试失败")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = main()
        print("\n按 Enter 键退出...")
        input()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
