# -*- coding: utf-8 -*-
"""
测试 yerui 用户权限修复
快速验证权限初始化修复是否生效
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests

# 配置
BACKEND_URL = "http://localhost:8000"
USERNAME = "yerui"
PASSWORD = "ye123456"

def test_login():
    """测试登录"""
    print("=" * 60)
    print("步骤 1: 测试登录")
    print("=" * 60)

    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 登录成功")
        print(f"  Token 类型: {data.get('token_type')}")
        print(f"  过期时间: {data.get('expires_in')} 秒")
        return data.get('access_token')
    else:
        print(f"[FAIL] 登录失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None

def test_user_info(token):
    """测试获取用户信息"""
    print("\n" + "=" * 60)
    print("步骤 2: 获取用户信息")
    print("=" * 60)

    response = requests.get(
        f"{BACKEND_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 用户信息获取成功")
        print(f"  用户名: {data.get('username')}")
        print(f"  全名: {data.get('full_name')}")
        print(f"  邮箱: {data.get('email')}")
        print(f"  是否激活: {data.get('is_active')}")
        print(f"  是否超级用户: {data.get('is_superuser')}")
        print(f"  角色数量: {len(data.get('roles', []))}")

        if data.get('roles'):
            print(f"\n  角色列表:")
            for role in data.get('roles', []):
                print(f"    - {role.get('display_name')} (level: {role.get('level')})")

        return data
    else:
        print(f"[FAIL] 获取用户信息失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None

def test_permissions(user_data):
    """测试权限列表"""
    print("\n" + "=" * 60)
    print("步骤 3: 验证权限列表")
    print("=" * 60)

    if not user_data or not user_data.get('roles'):
        print("[FAIL] 无用户信息或角色")
        return False

    # 获取第一个角色的权限
    roles = user_data.get('roles', [])
    if not roles:
        print("[FAIL] 用户没有角色")
        return False

    permissions = roles[0].get('permissions', [])
    print(f"  权限总数: {len(permissions)}")

    if len(permissions) == 0:
        print("[FAIL] 权限列表为空！修复失败！")
        return False

    print(f"[OK] 权限列表不为空")

    # 验证 PC-UI 关键权限
    print(f"\n  PC-UI 关键权限验证:")
    required_permissions = [
        # 项目管理权限
        ('projects:create', '创建项目'),
        ('projects:read', '查看项目'),
        ('projects:update', '更新项目'),
        ('projects:delete', '删除项目'),
        # 资产管理权限
        ('assets:upload', '上传资产'),
        ('assets:read', '查看资产'),
        ('assets:create', '创建资产'),
        ('assets:update', '更新资产'),
        ('assets:delete', '删除资产'),
        # 工程结构权限
        ('structures:create', '创建结构'),
        ('structures:read', '查看结构'),
        ('structures:update', '更新结构'),
        ('structures:delete', '删除结构'),
        # 功能权限
        ('ocr:run', '运行OCR'),
        ('llm:run', '运行LLM'),
    ]

    perm_dict = {p['code']: p['name'] for p in permissions}

    all_passed = True
    for code, name in required_permissions:
        if code in perm_dict:
            print(f"    [OK] {code}: {perm_dict[code]}")
        else:
            print(f"    [FAIL] {code}: 缺失！")
            all_passed = False

    if all_passed:
        print(f"\n[OK] 所有关键权限都存在")
    else:
        print(f"\n[FAIL] 部分关键权限缺失")

    # 显示所有权限（可选）
    if len(permissions) <= 30:
        print(f"\n  完整权限列表:")
        for perm in permissions:
            print(f"    - {perm['code']}: {perm.get('name', '')}")

    return all_passed

def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("yerui 用户权限修复测试")
    print("=" * 60)
    print(f"后端地址: {BACKEND_URL}")
    print(f"测试用户: {USERNAME}")
    print(f"测试密码: {PASSWORD}")
    print()

    try:
        # 步骤 1: 登录
        token = test_login()
        if not token:
            print("\n[FAIL] 测试失败：无法登录")
            return False

        # 步骤 2: 获取用户信息
        user_data = test_user_info(token)
        if not user_data:
            print("\n[FAIL] 测试失败：无法获取用户信息")
            return False

        # 步骤 3: 验证权限
        permissions_ok = test_permissions(user_data)

        # 总结
        print("\n" + "=" * 60)
        print("测试结果总结")
        print("=" * 60)

        checks = [
            ("登录", token is not None),
            ("获取用户信息", user_data is not None),
            ("is_superuser = True", user_data.get('is_superuser') == True),
            ("权限列表不为空", len(user_data.get('roles', [{}])[0].get('permissions', [])) > 0),
            ("PC-UI 关键权限完整", permissions_ok),
        ]

        all_passed = True
        for check_name, check_result in checks:
            status = "[OK]" if check_result else "[FAIL]"
            print(f"  {status} {check_name}")
            if not check_result:
                all_passed = False

        print()
        if all_passed:
            print("[SUCCESS] 所有测试通过！权限修复成功！")
            print("\n下一步:")
            print("  1. 启动 PC-UI: python -m desktop.nicegui_app.pc_app")
            print("  2. 访问: http://localhost:8080")
            print("  3. 使用 yerui/ye123456 登录")
            print("  4. 验证所有按钮都显示")
        else:
            print("[ERROR] 部分测试失败，请检查上述错误信息")

        return all_passed

    except requests.exceptions.ConnectionError:
        print(f"\n[FAIL] 无法连接到后端服务 ({BACKEND_URL})")
        print(f"  请确保后端服务正在运行")
        print(f"  启动命令: python -m uvicorn services.backend.app.main:app --host localhost --port 8000")
        return False
    except Exception as e:
        print(f"\n[FAIL] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
