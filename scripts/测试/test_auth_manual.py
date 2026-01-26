# -*- coding: utf-8 -*-
"""
PC-UI 认证功能手动测试脚本

用于验证认证系统是否正常工作
"""

import requests
import json

# 配置
BACKEND_URL = "http://localhost:8000"
PC_UI_URL = "http://localhost:8080"


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_backend_health():
    """测试后端健康检查"""
    print_section("测试 1: 后端健康检查")

    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务运行正常")
            print(f"  响应: {response.json()}")
            return True
        else:
            print(f"✗ 后端响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到后端服务")
        print(f"  请确保后端运行在 {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_login_endpoint():
    """测试登录接口"""
    print_section("测试 2: 登录接口")

    # 测试正确的凭证
    print("\n[2.1] 测试正确的凭证 (admin/admin123)")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ 登录成功")
            print(f"  Access Token: {data.get('access_token', '')[:50]}...")
            print(f"  Refresh Token: {data.get('refresh_token', '')[:50]}...")
            print(f"  用户: {data.get('user', {}).get('username')}")
            return data.get('access_token')
        else:
            print(f"✗ 登录失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None


def test_wrong_credentials():
    """测试错误凭证"""
    print_section("测试 3: 错误凭证处理")

    print("\n[3.1] 测试错误的密码")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "wrong_password"},
            timeout=10
        )

        if response.status_code == 401:
            print("✓ 正确返回 401 未授权")
            print(f"  错误消息: {response.json().get('detail')}")
        elif response.status_code == 200:
            print("✗ 错误：错误凭证竟然登录成功了！")
        else:
            print(f"? 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 错误: {e}")


def test_protected_endpoint(token):
    """测试受保护的接口"""
    print_section("测试 4: 受保护接口访问")

    if not token:
        print("✗ 没有有效的 token，跳过此测试")
        return

    print("\n[4.1] 使用 token 访问项目列表")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/projects/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )

        if response.status_code == 200:
            projects = response.json()
            print(f"✓ 成功获取项目列表")
            print(f"  项目数量: {len(projects)}")
            if projects:
                print(f"  第一个项目: {projects[0].get('name', 'N/A')}")
        elif response.status_code == 401:
            print("✗ 401 未授权 - token 可能无效")
        else:
            print(f"? 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 错误: {e}")


def test_unauthorized_access():
    """测试未授权访问"""
    print_section("测试 5: 未授权访问（无 token）")

    print("\n[5.1] 不带 token 访问项目列表")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/projects/",
            timeout=10
        )

        if response.status_code == 401:
            print("✓ 正确返回 401 未授权")
            print("  后端认证检查工作正常")
        else:
            print(f"✗ 错误：应该返回 401，但返回了 {response.status_code}")
    except Exception as e:
        print(f"✗ 错误: {e}")


def test_pc_ui_access():
    """测试 PC-UI 访问"""
    print_section("测试 6: PC-UI 服务")

    try:
        response = requests.get(PC_UI_URL, timeout=5)
        if response.status_code == 200:
            print("✓ PC-UI 服务运行正常")
            print(f"  访问地址: {PC_UI_URL}")
            print("  请在浏览器中打开上述地址进行手动测试")
        else:
            print(f"? PC-UI 返回状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ PC-UI 服务未运行")
        print(f"  请启动 PC-UI: python -m desktop.nicegui_app.pc_app")
    except Exception as e:
        print(f"✗ 错误: {e}")


def print_manual_checklist():
    """打印手动测试清单"""
    print_section("手动测试清单")

    print("""
请在浏览器中完成以下测试：

1. 访问 http://localhost:8080
   □ 应该自动跳转到 /login 页面

2. 登录功能测试
   □ 输入正确的用户名和密码 (admin/admin123)
   □ 点击"登录"按钮
   □ 应该显示"登录成功"通知
   □ 应该跳转到主页

3. 登录状态验证
   □ 页面右上角显示用户名 (admin)
   □ 页面右上角显示登出按钮
   □ 能看到项目列表（如果有数据）

4. 会话持久化测试
   □ 按 F5 刷新页面
   □ 应该保持登录状态
   □ 不需要重新登录

5. 登出功能测试
   □ 点击右上角的登出按钮
   □ 应该显示"已登出"通知
   □ 应该跳转回 /login 页面
   □ 刷新页面后仍在登录页

6. 错误凭证测试
   □ 重新访问登录页
   □ 输入错误的用户名或密码
   □ 应该显示错误消息
   □ 不应该登录成功
    """)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" BDC-AI PC-UI 认证功能测试")
    print("=" * 60)

    # 运行所有测试
    backend_ok = test_backend_health()
    if not backend_ok:
        print("\n❌ 后端服务未运行，测试终止")
        print("请先启动后端：")
        print("  python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload")
        return

    token = test_login_endpoint()
    test_wrong_credentials()

    if token:
        test_protected_endpoint(token)

    test_unauthorized_access()
    test_pc_ui_access()
    print_manual_checklist()

    # 总结
    print_section("测试总结")
    print("""
✓ 后端 API 测试已完成
□ 浏览器手动测试需要您完成

如果所有后端测试都通过（显示 ✓），说明认证系统工作正常。
请按照上述清单在浏览器中完成 UI 测试。
    """)


if __name__ == "__main__":
    main()
