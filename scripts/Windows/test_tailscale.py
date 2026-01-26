"""
Tailscale VPN 连接测试脚本
简单快速地测试 Tailscale 是否工作正常
"""

import requests
import subprocess
import json
import sys
from datetime import datetime

# 配置
BACKEND_TAILSCALE_IP = "100.93.101.76"
BACKEND_PORT = "8000"
BACKEND_URL = f"http://{BACKEND_TAILSCALE_IP}:{BACKEND_PORT}"


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


def test_tailscale_status():
    """测试 1: 检查 Tailscale 服务状态"""
    print_header("测试 1: Tailscale 服务状态")

    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            print_success("Tailscale 服务运行中")
            print_info(f"版本: {data.get('Version', 'unknown')}")
            print_info(f"主机名: {data['Self'].get('HostName', 'unknown')}")
            print_info(f"Tailscale IPs: {', '.join(data['Self'].get('TailscaleIPs', []))}")
            print_info(f"状态: {data.get('BackendState', 'unknown')}")

            return True, data['Self'].get('TailscaleIPs', [None])[0]
        else:
            print_error("Tailscale 服务未运行")
            return False, None

    except FileNotFoundError:
        print_error("Tailscale 未安装或不在 PATH 中")
        return False, None
    except Exception as e:
        print_error(f"检查失败: {e}")
        return False, None


def test_ping_backend(tailscale_ip):
    """测试 2: Ping 后端 Tailscale IP"""
    print_header("测试 2: Ping 后端 Tailscale IP")

    print_info(f"后端 Tailscale IP: {BACKEND_TAILSCALE_IP}")
    print_info(f"本机 Tailscale IP: {tailscale_ip}")

    if BACKEND_TAILSCALE_IP == tailscale_ip:
        print_info("本机和后端是同一台设备")
        return True

    try:
        # Windows 使用 ping 命令
        result = subprocess.run(
            ["ping", "-n", "2", BACKEND_TAILSCALE_IP],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success(f"可以 ping 通 {BACKEND_TAILSCALE_IP}")
            return True
        else:
            print_error(f"无法 ping 通 {BACKEND_TAILSCALE_IP}")
            return False

    except Exception as e:
        print_error(f"Ping 失败: {e}")
        return False


def test_backend_api():
    """测试 3: 访问后端 API"""
    print_header("测试 3: 后端 API 连接")

    print_info(f"后端地址: {BACKEND_URL}")

    try:
        # 测试根路径
        response = requests.get(f"{BACKEND_URL}/", timeout=5)

        if response.status_code == 200:
            print_success("后端 API 连接成功")
            print_info(f"响应: {response.json()}")

            # 测试健康检查
            health_response = requests.get(f"{BACKEND_URL}/api/v1/health/", timeout=5)
            if health_response.status_code == 200:
                print_success("健康检查端点正常")
                print_info(f"健康状态: {health_response.json()}")

            return True
        else:
            print_error(f"后端返回错误状态码: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("无法连接到后端")
        print_info("可能的原因:")
        print_info("  1. 后端服务未启动")
        print_info("  2. 后端未监听 0.0.0.0（只监听 127.0.0.1）")
        print_info("  3. 防火墙阻止了连接")
        return False
    except requests.exceptions.Timeout:
        print_error("连接超时")
        return False
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False


def test_login():
    """测试 4: 认证登录"""
    print_header("测试 4: 认证系统")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print_success("登录成功")
            print_info(f"Token 类型: {data.get('token_type')}")
            print_info(f"有效期: {data.get('expires_in')} 秒")
            return True
        else:
            print_error(f"登录失败: {response.json().get('detail', '未知错误')}")
            return False

    except Exception as e:
        print_error(f"登录测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Tailscale VPN 连接测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BACKEND_URL}")

    results = []

    # 测试 1: Tailscale 状态
    result, tailscale_ip = test_tailscale_status()
    results.append(("Tailscale 状态", result))

    if not result:
        print("\n" + "=" * 60)
        print("[ERROR] Tailscale 未运行，无法继续测试")
        print("=" * 60)
        return False

    # 测试 2: Ping 后端
    if tailscale_ip != BACKEND_TAILSCALE_IP:
        result = test_ping_backend(tailscale_ip)
        results.append(("Ping 后端", result))
    else:
        print("\n[SKIP] 跳过 Ping 测试（本机和后端是同一设备）")

    # 测试 3: 后端 API
    result = test_backend_api()
    results.append(("后端 API", result))

    if result:
        # 测试 4: 认证
        result = test_login()
        results.append(("认证登录", result))

    # 打印总结
    print_header("测试总结")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    failed = total - passed

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
        print("[SUCCESS] Tailscale VPN 连接完全正常！")
        print()
        print("你现在可以从其他设备通过 Tailscale 访问后端:")
        print(f"  后端地址: {BACKEND_URL}")
        print(f"  API 文档: {BACKEND_URL}/docs")
        print("=" * 60)
        return True
    else:
        print("[WARNING] 部分测试失败，请检查配置")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
