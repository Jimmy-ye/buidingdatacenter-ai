# -*- coding: utf-8 -*-
"""
测试前端权限控制功能

验证 AuthManager 的权限检查方法和用户信息显示
"""
import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from desktop.nicegui_app.auth_manager import auth_manager


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_admin_login():
    """测试管理员登录和权限"""
    print_section("测试 1: 管理员登录与权限")

    print("\n[1.1] 使用 admin/admin123 登录...")
    success, msg = auth_manager.login("admin", "admin123")

    if success:
        print(f"[OK] 登录成功: {msg}")

        # 显示用户信息
        user = auth_manager.user
        if user:
            print(f"\n用户信息:")
            print(f"  用户名: {user.get('username')}")
            print(f"  邮箱: {user.get('email')}")
            print(f"  是否超级管理员: {user.get('is_superuser', False)}")

        # 显示角色
        roles = auth_manager.get_roles()
        print(f"\n角色列表 ({len(roles)} 个):")
        for role in roles:
            print(f"  - {role}")

        # 显示权限（前20个）
        permissions = auth_manager.get_all_permissions()
        print(f"\n权限列表 (共 {len(permissions)} 个，显示前20个):")
        for perm in permissions[:20]:
            print(f"  - {perm}")
        if len(permissions) > 20:
            print(f"  ... 还有 {len(permissions) - 20} 个权限")

        return True
    else:
        print(f"[FAIL] 登录失败: {msg}")
        return False


def test_permission_checks():
    """测试权限检查方法"""
    print_section("测试 2: 权限检查方法")

    if not auth_manager.is_authenticated():
        print("[ ] 未登录，跳过此测试")
        return False

    print("\n[2.1] 测试单个权限检查")
    test_permissions = [
        ("projects:create", "创建项目"),
        ("projects:update", "编辑项目"),
        ("projects:delete", "删除项目"),
        ("structures:create", "创建工程结构"),
        ("structures:update", "编辑工程结构"),
        ("structures:delete", "删除工程结构"),
        ("assets:upload", "上传资产"),
        ("assets:delete", "删除资产"),
        ("ocr:run", "运行 OCR"),
        ("llm:run", "生成 LLM 报告"),
    ]

    for perm_code, perm_name in test_permissions:
        has_perm = auth_manager.has_permission(perm_code)
        status = "[+]" if has_perm else "[ ]"
        print(f"  {status} {perm_code} ({perm_name}): {has_perm}")

    print("\n[2.2] 测试超级管理员检查")
    is_superuser = auth_manager.is_superuser()
    print(f"  {'[+]' if is_superuser else '[ ]'} 是否超级管理员: {is_superuser}")

    print("\n[2.3] 测试角色检查")
    test_roles = ["admin", "manager", "engineer", "viewer"]
    for role_name in test_roles:
        has_role = auth_manager.has_role(role_name)
        status = "[+]" if has_role else "[ ]"
        print(f"  {status} 是否拥有角色 '{role_name}': {has_role}")

    print("\n[2.4] 测试用户信息显示")
    display_text = auth_manager.get_user_info_display()
    print(f"  显示文本: {display_text}")

    return True


def test_permission_edge_cases():
    """测试边界情况"""
    print_section("测试 3: 边界情况")

    print("\n[3.1] 测试不存在的权限")
    has_fake_perm = auth_manager.has_permission("fake:permission")
    print(f"  不存在的权限: {has_fake_perm} (应该为 False)")

    print("\n[3.2] 测试 has_any_permission")
    test_perms = ["projects:view", "projects:create", "fake:permission"]
    has_any = auth_manager.has_any_permission(test_perms)
    print(f"  拥有任一权限 {test_perms}: {has_any} (应该至少有一个)")

    print("\n[3.3] 测试 has_all_permissions")
    test_perms_all = ["projects:create", "projects:update"]
    has_all = auth_manager.has_all_permissions(test_perms_all)
    print(f"  拥有所有权限 {test_perms_all}: {has_all}")

    return True


def test_logout():
    """测试登出"""
    print_section("测试 4: 登出")

    print("\n[4.1] 登出当前用户...")
    auth_manager.logout()

    print(f"[OK] 已登出")
    print(f"  认证状态: {auth_manager.is_authenticated()} (应该为 False)")
    print(f"  用户信息: {auth_manager.user} (应该为 None)")
    print(f"  角色列表: {auth_manager.get_roles()} (应该为空)")

    return True


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" BDC-AI 前端权限控制测试")
    print("=" * 70)

    # 测试 1: 管理员登录
    if not test_admin_login():
        print("\n[FAIL] 登录失败，测试终止")
        print("\n请确保：")
        print("  1. 后端服务运行中 (http://localhost:8000)")
        print("  2. 数据库中存在 admin 用户")
        print("  3. admin 用户密码是 admin123")
        return

    # 测试 2: 权限检查
    test_permission_checks()

    # 测试 3: 边界情况
    test_permission_edge_cases()

    # 测试 4: 登出
    test_logout()

    # 总结
    print_section("测试总结")
    print("""
[OK] 权限检查方法测试完成
□ UI 测试需要您在浏览器中完成

请访问 http://localhost:8080 进行 UI 测试：
  1. 登录系统 (admin/admin123)
  2. 检查页面右上角是否显示用户名和角色
  3. 检查是否可以看到所有按钮
  4. 尝试点击各个按钮，验证功能正常

详细测试清单: scripts/测试/test_permission_control.md
    """)


if __name__ == "__main__":
    main()
