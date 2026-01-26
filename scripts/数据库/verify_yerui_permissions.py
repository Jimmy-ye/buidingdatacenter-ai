"""
验证用户权限配置
检查 yerui 和 admin 用户的权限配置是否正确
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from shared.db.session import SessionLocal
from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission

def verify_user_permissions():
    """验证 yerui 和 admin 用户的权限配置"""

    print("=" * 60)
    print("用户权限验证")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 检查的用户列表
        target_users = ['yerui', 'admin']

        for username in target_users:
            print(f"\n{'='*60}")
            print(f"检查用户: {username}")
            print('='*60)

            # 1. 检查用户是否存在
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"  [ERROR] 用户不存在")
                continue

            print(f"  [✓] 用户存在")
            print(f"    ID: {user.id}")
            print(f"    Email: {user.email or '未设置'}")
            print(f"    全名: {user.full_name or '未设置'}")
            print(f"    is_active: {user.is_active}")
            print(f"    is_superuser: {user.is_superuser}")

            if not user.is_superuser:
                print(f"  [WARNING] 用户不是超级用户！")

            # 2. 检查角色
            user_roles = db.query(Role).join(
                UserRole
            ).filter(
                UserRole.user_id == user.id
            ).all()

            print(f"\n  [✓] 用户角色数量: {len(user_roles)}")
            for role in user_roles:
                print(f"    - {role.display_name} (name: {role.name}, level: {role.level})")

            # 3. 检查权限
            if user.is_superuser:
                # 超级用户拥有所有权限
                total_permissions = db.query(Permission).count()
                all_permissions = db.query(Permission).order_by(Permission.resource, Permission.action).all()

                print(f"\n  [✓] 超级用户拥有所有权限")
                print(f"    总权限数: {total_permissions}")

                # 显示前 10 个权限
                print(f"    前 10 个权限:")
                for perm in all_permissions[:10]:
                    print(f"      - {perm.code}: {perm.name}")
                if len(all_permissions) > 10:
                    print(f"      ... 还有 {len(all_permissions) - 10} 个权限")

            else:
                # 查询角色的权限
                permissions = db.query(Permission).join(
                    RolePermission
                ).join(
                    Role
                ).join(
                    UserRole
                ).filter(
                    UserRole.user_id == user.id
                ).distinct().order_by(Permission.resource, Permission.action).all()

                print(f"\n  [✓] 用户权限数量: {len(permissions)}")
                for perm in permissions:
                    print(f"    - {perm.code}: {perm.name}")

                if len(permissions) == 0:
                    print(f"  [ERROR] 用户没有任何权限！")

        print(f"\n{'='*60}")
        print("PC-UI 关键权限检查")
        print('='*60)

        # 4. 检查 PC-UI 需要的关键权限
        required_permissions = [
            'projects:create', 'projects:read', 'projects:update', 'projects:delete',
            'structures:create', 'structures:read', 'structures:update', 'structures:delete',
            'assets:upload', 'assets:read',
            'ocr:run', 'llm:run'
        ]

        missing_permissions = []
        existing_permissions = []

        for perm_code in required_permissions:
            perm = db.query(Permission).filter(Permission.code == perm_code).first()
            if perm:
                existing_permissions.append(perm_code)
            else:
                missing_permissions.append(perm_code)

        print(f"\n  必需权限检查:")
        print(f"    已存在: {len(existing_permissions)}/{len(required_permissions)}")

        if missing_permissions:
            print(f"\n  [WARNING] 缺少 {len(missing_permissions)} 个权限:")
            for code in missing_permissions:
                print(f"    - {code}")
            return False
        else:
            print(f"  [✓] 所有必要权限都存在")

        print()
        print("=" * 60)
        print("[SUCCESS] 权限配置验证通过！")
        print("=" * 60)
        print()
        print("可以尝试使用以下账号登录:")
        print("  用户名: yerui")
        print("  密码: ye123456")
        print()
        print("  用户名: admin")
        print("  密码: admin123")
        print("=" * 60)

        return True

    finally:
        db.close()

if __name__ == "__main__":
    success = verify_user_permissions()
    sys.exit(0 if success else 1)
