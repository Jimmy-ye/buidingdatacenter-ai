"""
初始化认证系统的默认数据
创建默认管理员账号和角色权限
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from shared.db.session import engine
from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission
from shared.security.password import get_password_hash
from uuid import uuid4


def init_permissions(db: Session):
    """初始化权限数据"""
    print("正在初始化权限...")

    permissions_data = [
        # 用户管理权限
        {"code": "user:create", "name": "创建用户", "resource": "user", "action": "create", "description": "创建用户"},
        {"code": "user:read", "name": "查看用户", "resource": "user", "action": "read", "description": "查看用户"},
        {"code": "user:update", "name": "更新用户", "resource": "user", "action": "update", "description": "更新用户"},
        {"code": "user:delete", "name": "删除用户", "resource": "user", "action": "delete", "description": "删除用户"},

        # 角色管理权限
        {"code": "role:create", "name": "创建角色", "resource": "role", "action": "create", "description": "创建角色"},
        {"code": "role:read", "name": "查看角色", "resource": "role", "action": "read", "description": "查看角色"},
        {"code": "role:update", "name": "更新角色", "resource": "role", "action": "update", "description": "更新角色"},
        {"code": "role:delete", "name": "删除角色", "resource": "role", "action": "delete", "description": "删除角色"},

        # 项目管理权限
        {"code": "project:create", "name": "创建项目", "resource": "project", "action": "create", "description": "创建项目"},
        {"code": "project:read", "name": "查看项目", "resource": "project", "action": "read", "description": "查看项目"},
        {"code": "project:update", "name": "更新项目", "resource": "project", "action": "update", "description": "更新项目"},
        {"code": "project:delete", "name": "删除项目", "resource": "project", "action": "delete", "description": "删除项目"},

        # 资产管理权限
        {"code": "asset:create", "name": "创建资产", "resource": "asset", "action": "create", "description": "创建资产"},
        {"code": "asset:read", "name": "查看资产", "resource": "asset", "action": "read", "description": "查看资产"},
        {"code": "asset:update", "name": "更新资产", "resource": "asset", "action": "update", "description": "更新资产"},
        {"code": "asset:delete", "name": "删除资产", "resource": "asset", "action": "delete", "description": "删除资产"},

        # 系统管理权限
        {"code": "system:config", "name": "系统配置", "resource": "system", "action": "config", "description": "系统配置"},
        {"code": "audit:read", "name": "查看审计日志", "resource": "audit", "action": "read", "description": "查看审计日志"},
    ]

    for perm_data in permissions_data:
        existing = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
        if not existing:
            perm = Permission(**perm_data)
            db.add(perm)
            print(f"  [创建] 权限: {perm_data['code']} - {perm_data['description']}")
        else:
            print(f"  [已存在] 权限: {perm_data['code']}")

    db.commit()
    print("权限初始化完成！\n")


def init_roles(db: Session):
    """初始化角色数据"""
    print("正在初始化角色...")

    # 获取所有权限
    all_permissions = db.query(Permission).all()

    # 超级管理员角色
    superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
    if not superadmin_role:
        superadmin_role = Role(
            name="superadmin",
            display_name="超级管理员",
            description="拥有所有权限的系统管理员",
            level=999
        )
        db.add(superadmin_role)
        db.flush()
        print(f"  [创建] 角色: {superadmin_role.display_name}")

        # 分配所有权限给超级管理员
        for perm in all_permissions:
            role_perm = RolePermission(role_id=superadmin_role.id, permission_id=perm.id)
            db.add(role_perm)
        print(f"    -> 已分配 {len(all_permissions)} 个权限")
    else:
        print(f"  [已存在] 角色: {superadmin_role.display_name}")

    # 管理员角色
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            display_name="管理员",
            description="拥有大部分管理权限的管理员",
            level=100
        )
        db.add(admin_role)
        db.flush()
        print(f"  [创建] 角色: {admin_role.display_name}")

        # 分配部分权限（排除删除操作）
        for perm in all_permissions:
            if not perm.action == "delete":
                role_perm = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.add(role_perm)
        print(f"    -> 已分配部分权限")
    else:
        print(f"  [已存在] 角色: {admin_role.display_name}")

    # 普通用户角色
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(
            name="user",
            display_name="普通用户",
            description="普通用户，只能查看和编辑基本数据",
            level=10
        )
        db.add(user_role)
        db.flush()
        print(f"  [创建] 角色: {user_role.display_name}")

        # 分配只读权限
        read_permissions = db.query(Permission).filter(Permission.action == "read").all()
        for perm in read_permissions:
            role_perm = RolePermission(role_id=user_role.id, permission_id=perm.id)
            db.add(role_perm)
        print(f"    -> 已分配 {len(read_permissions)} 个只读权限")
    else:
        print(f"  [已存在] 角色: {user_role.display_name}")

    db.commit()
    print("角色初始化完成！\n")


def init_users(db: Session):
    """初始化用户数据"""
    print("正在初始化用户...")

    # 检查是否已有管理员用户
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        print(f"  [已存在] 管理员用户: admin")
        print(f"    ID: {existing_admin.id}")
        print(f"    Email: {existing_admin.email or '未设置'}")
        return

    # 创建默认管理员
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        email="admin@bdc-ai.com",
        full_name="系统管理员",
        phone="",
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.flush()
    print(f"  [创建] 管理员用户: admin")
    print(f"    密码: admin123 (请及时修改)")
    print(f"    ID: {admin_user.id}")

    # 分配超级管理员角色
    superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
    if superadmin_role:
        user_role = UserRole(user_id=admin_user.id, role_id=superadmin_role.id)
        db.add(user_role)
        print(f"    -> 已分配角色: {superadmin_role.display_name}")

    db.commit()
    print("用户初始化完成！\n")


def main():
    """主函数"""
    print("=" * 80)
    print("BDC-AI 认证系统初始化")
    print("=" * 80)
    print()

    # 创建数据库会话
    from shared.db.session import SessionLocal
    db = SessionLocal()

    try:
        # 初始化权限
        init_permissions(db)

        # 初始化角色
        init_roles(db)

        # 初始化用户
        init_users(db)

        print("=" * 80)
        print("初始化完成！")
        print("=" * 80)
        print()
        print("默认管理员账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print()
        print("请使用以下命令测试登录:")
        print("  curl -X POST http://localhost:8000/api/v1/auth/login \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"username":"admin","password":"admin123"}\'')
        print()

    except Exception as e:
        print(f"\n[错误] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
