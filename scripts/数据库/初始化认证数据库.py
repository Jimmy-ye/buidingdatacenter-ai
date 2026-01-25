"""初始化认证和权限数据库"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from shared.db.session import SessionLocal
from shared.db.base import Base
from shared.db import models_project, models_asset, models_auth  # noqa: F401 导入所有模型以确保表被创建
from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission
from shared.security.password import get_password_hash


def init_permissions(db: Session) -> dict:
    """
    初始化权限数据

    Returns:
        dict: 权限代码到权限对象的映射
    """
    print("初始化权限...")

    permissions_data = [
        # 项目管理权限
        {"code": "projects.read", "name": "查看项目", "resource": "projects", "action": "read"},
        {"code": "projects.create", "name": "创建项目", "resource": "projects", "action": "create"},
        {"code": "projects.update", "name": "更新项目", "resource": "projects", "action": "update"},
        {"code": "projects.delete", "name": "删除项目", "resource": "projects", "action": "delete"},
        {"code": "projects.admin", "name": "项目管理（全部）", "resource": "projects", "action": "admin"},

        # 资产管理权限
        {"code": "assets.read", "name": "查看资产", "resource": "assets", "action": "read"},
        {"code": "assets.create", "name": "创建资产", "resource": "assets", "action": "create"},
        {"code": "assets.update", "name": "更新资产", "resource": "assets", "action": "update"},
        {"code": "assets.delete", "name": "删除资产", "resource": "assets", "action": "delete"},
        {"code": "assets.upload", "name": "上传资产", "resource": "assets", "action": "upload"},

        # 用户管理权限
        {"code": "users.read", "name": "查看用户", "resource": "users", "action": "read"},
        {"code": "users.create", "name": "创建用户", "resource": "users", "action": "create"},
        {"code": "users.update", "name": "更新用户", "resource": "users", "action": "update"},
        {"code": "users.delete", "name": "删除用户", "resource": "users", "action": "delete"},
        {"code": "users.admin", "name": "用户管理（全部）", "resource": "users", "action": "admin"},

        # 角色权限管理
        {"code": "roles.read", "name": "查看角色", "resource": "roles", "action": "read"},
        {"code": "roles.admin", "name": "角色管理（全部）", "resource": "roles", "action": "admin"},

        # 审计日志权限
        {"code": "audit_logs.read", "name": "查看审计日志", "resource": "audit_logs", "action": "read"},

        # 报告权限
        {"code": "reports.read", "name": "查看报告", "resource": "reports", "action": "read"},
        {"code": "reports.create", "name": "生成报告", "resource": "reports", "action": "create"},
        {"code": "reports.export", "name": "导出报告", "resource": "reports", "action": "export"},

        # 系统管理权限
        {"code": "system.config", "name": "系统配置", "resource": "system", "action": "config"},
        {"code": "system.monitor", "name": "系统监控", "resource": "system", "action": "monitor"},
    ]

    permissions_map = {}
    for perm_data in permissions_data:
        perm = Permission(**perm_data)
        db.add(perm)
        db.flush()  # 获取 ID
        permissions_map[perm.code] = perm

    db.commit()
    print(f"✓ 创建了 {len(permissions_data)} 个权限")

    return permissions_map


def init_roles(db: Session, permissions_map: dict) -> dict:
    """
    初始化角色数据

    Args:
        db: 数据库会话
        permissions_map: 权限映射

    Returns:
        dict: 角色名称到角色对象的映射
    """
    print("\n初始化角色...")

    roles_data = [
        {
            "name": "superuser",
            "display_name": "超级管理员",
            "description": "系统管理员，拥有所有权限",
            "level": 100,
            "permissions": list(permissions_map.values())  # 所有权限
        },
        {
            "name": "admin",
            "display_name": "管理员",
            "description": "项目管理员，可以管理项目、资产和用户",
            "level": 80,
            "permissions": [
                permissions_map["projects.read"],
                permissions_map["projects.create"],
                permissions_map["projects.update"],
                permissions_map["projects.delete"],
                permissions_map["assets.read"],
                permissions_map["assets.create"],
                permissions_map["assets.update"],
                permissions_map["assets.delete"],
                permissions_map["assets.upload"],
                permissions_map["users.read"],
                permissions_map["users.update"],
                permissions_map["reports.read"],
                permissions_map["reports.create"],
                permissions_map["reports.export"],
            ]
        },
        {
            "name": "project_manager",
            "display_name": "项目经理",
            "description": "项目经理，可以管理项目和查看资产",
            "level": 60,
            "permissions": [
                permissions_map["projects.read"],
                permissions_map["projects.create"],
                permissions_map["projects.update"],
                permissions_map["assets.read"],
                permissions_map["assets.upload"],
                permissions_map["reports.read"],
                permissions_map["reports.create"],
            ]
        },
        {
            "name": "engineer",
            "display_name": "现场工程师",
            "description": "现场工程师，可以上传资产和查看项目",
            "level": 40,
            "permissions": [
                permissions_map["projects.read"],
                permissions_map["assets.read"],
                permissions_map["assets.create"],
                permissions_map["assets.upload"],
            ]
        },
        {
            "name": "analyst",
            "display_name": "数据分析师",
            "description": "数据分析师，可以查看所有数据和生成报告",
            "level": 50,
            "permissions": [
                permissions_map["projects.read"],
                permissions_map["assets.read"],
                permissions_map["reports.read"],
                permissions_map["reports.create"],
                permissions_map["reports.export"],
            ]
        },
        {
            "name": "viewer",
            "display_name": "访客",
            "description": "访客，只有只读权限",
            "level": 20,
            "permissions": [
                permissions_map["projects.read"],
                permissions_map["assets.read"],
            ]
        },
    ]

    roles_map = {}
    for role_data in roles_data:
        permissions = role_data.pop("permissions")

        role = Role(**role_data)
        db.add(role)
        db.flush()  # 获取 ID

        # 分配权限
        for perm in permissions:
            role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
            db.add(role_perm)

        roles_map[role.name] = role

    db.commit()
    print(f"✓ 创建了 {len(roles_data)} 个角色")

    return roles_map


def init_users(db: Session, roles_map: dict):
    """
    初始化用户数据

    Args:
        db: 数据库会话
        roles_map: 角色映射
    """
    print("\n初始化用户...")

    # 创建默认管理员账号
    admin_username = "admin"
    admin_password = "admin123"  # 生产环境应该修改

    # 检查是否已存在
    existing_admin = db.query(User).filter(User.username == admin_username).first()
    if existing_admin:
        print(f"⚠ 管理员账号 '{admin_username}' 已存在，跳过创建")
        return

    admin_user = User(
        username=admin_username,
        hashed_password=get_password_hash(admin_password),
        full_name="系统管理员",
        email="admin@bdc-ai.local",
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.flush()  # 获取 ID

    # 分配超级管理员角色
    user_role = UserRole(user_id=admin_user.id, role_id=roles_map["superuser"].id)
    db.add(user_role)

    db.commit()
    print(f"✓ 创建了默认管理员账号:")
    print(f"  用户名: {admin_username}")
    print(f"  密码: {admin_password}")
    print(f"  ⚠ 请登录后立即修改密码！")

    # 创建测试用户（可选）
    test_users = [
        {
            "username": "manager1",
            "password": "manager123",
            "full_name": "项目经理1",
            "role": "project_manager"
        },
        {
            "username": "engineer1",
            "password": "engineer123",
            "full_name": "现场工程师1",
            "role": "engineer"
        },
        {
            "username": "analyst1",
            "password": "analyst123",
            "full_name": "数据分析师1",
            "role": "analyst"
        },
    ]

    for user_data in test_users:
        role_name = user_data.pop("role")
        user = User(
            username=user_data["username"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.flush()

        # 分配角色
        user_role = UserRole(user_id=user.id, role_id=roles_map[role_name].id)
        db.add(user_role)

    db.commit()
    print(f"✓ 创建了 {len(test_users)} 个测试用户:")
    for user in test_users:
        print(f"  - {user['username']} / {user['password']}")


def main():
    """主函数"""
    print("=" * 60)
    print("BDC-AI 认证和权限数据库初始化")
    print("=" * 60)

    # 创建所有表
    print("\n创建数据库表...")
    from shared.db import models_auth  # noqa: F401
    Base.metadata.create_all(bind=SessionLocal().bind)
    print("✓ 数据库表创建完成")

    # 获取数据库会话
    db = SessionLocal()

    try:
        # 初始化权限
        permissions_map = init_permissions(db)

        # 初始化角色
        roles_map = init_roles(db, permissions_map)

        # 初始化用户
        init_users(db, roles_map)

        print("\n" + "=" * 60)
        print("初始化完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
