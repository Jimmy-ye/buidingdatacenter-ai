"""认证和权限业务逻辑"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission, AuditLog
from shared.security.password import verify_password, get_password_hash
from shared.security.jwt import create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from shared.config.settings import get_settings

settings = get_settings()


class AuthService:
    """认证服务"""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户名和密码

        Args:
            db: 数据库会话
            username: 用户名
            password: 密码

        Returns:
            Optional[User]: 验证成功返回用户对象，失败返回 None
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    @staticmethod
    def login(db: Session, username: str, password: str, ip_address: str = None, user_agent: str = None) -> dict:
        """
        用户登录

        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            ip_address: IP地址（审计用）
            user_agent: 用户代理（审计用）

        Returns:
            dict: 包含 access_token 和 refresh_token 的字典

        Raises:
            ValueError: 用户名或密码错误
        """
        # 验证用户
        user = AuthService.authenticate_user(db, username, password)
        if not user:
            # 记录失败的登录尝试（可选）
            raise ValueError("用户名或密码错误")

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()

        # 记录审计日志
        AuthService.create_audit_log(
            db=db,
            user_id=user.id,
            action="login",
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 生成 Token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username,
                "is_superuser": user.is_superuser
            }
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> dict:
        """
        刷新访问令牌

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            dict: 包含新的 access_token 和 refresh_token 的字典

        Raises:
            ValueError: 刷新令牌无效
        """
        from shared.security.jwt import verify_token

        user_id = verify_token(refresh_token, token_type="refresh")
        if not user_id:
            raise ValueError("无效的刷新令牌")

        # 查询用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("用户不存在或已禁用")

        # 生成新的 Token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username,
                "is_superuser": user.is_superuser
            }
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def create_user(db: Session, user_data: dict, creator_id: UUID) -> User:
        """
        创建用户（管理员功能）

        Args:
            db: 数据库会话
            user_data: 用户数据
            creator_id: 创建者ID

        Returns:
            User: 创建的用户对象
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_user:
            raise ValueError(f"用户名 '{user_data['username']}' 已存在")

        # 创建用户
        user = User(
            username=user_data["username"],
            hashed_password=get_password_hash(user_data["password"]),
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            phone=user_data.get("phone"),
            is_active=user_data.get("is_active", True),
            is_superuser=user_data.get("is_superuser", False)
        )

        db.add(user)
        db.flush()  # 获取 user.id

        # 分配角色
        role_ids = user_data.get("role_ids", [])
        for role_id in role_ids:
            user_role = UserRole(user_id=user.id, role_id=role_id)
            db.add(user_role)

        db.commit()

        # 记录审计日志
        AuthService.create_audit_log(
            db=db,
            user_id=creator_id,
            action="create_user",
            resource_type="user",
            resource_id=str(user.id),
            details={"username": user.username}
        )

        return user

    @staticmethod
    def update_user(db: Session, user_id: UUID, user_data: dict, updater_id: UUID) -> Optional[User]:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID
            user_data: 更新数据
            updater_id: 更新者ID

        Returns:
            Optional[User]: 更新后的用户对象
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # 更新基本信息
        if "email" in user_data:
            user.email = user_data["email"]
        if "full_name" in user_data:
            user.full_name = user_data["full_name"]
        if "phone" in user_data:
            user.phone = user_data["phone"]
        if "is_active" in user_data:
            user.is_active = user_data["is_active"]

        # 更新角色
        if "role_ids" in user_data:
            # 删除旧角色
            db.query(UserRole).filter(UserRole.user_id == user_id).delete()
            # 添加新角色
            for role_id in user_data["role_ids"]:
                user_role = UserRole(user_id=user_id, role_id=role_id)
                db.add(user_role)

        user.updated_at = datetime.utcnow()
        db.commit()

        # 记录审计日志
        AuthService.create_audit_log(
            db=db,
            user_id=updater_id,
            action="update_user",
            resource_type="user",
            resource_id=str(user_id),
            details=user_data
        )

        return user

    @staticmethod
    def delete_user(db: Session, user_id: UUID, deleter_id: UUID) -> bool:
        """
        删除用户

        Args:
            db: 数据库会话
            user_id: 用户ID
            deleter_id: 删除者ID

        Returns:
            bool: 是否删除成功
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()

        # 记录审计日志
        AuthService.create_audit_log(
            db=db,
            user_id=deleter_id,
            action="delete_user",
            resource_type="user",
            resource_id=str(user_id)
        )

        return True

    @staticmethod
    def change_password(db: Session, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            bool: 是否修改成功

        Raises:
            ValueError: 旧密码错误
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("旧密码错误")

        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        # 记录审计日志
        AuthService.create_audit_log(
            db=db,
            user_id=user_id,
            action="change_password",
            resource_type="user",
            resource_id=str(user_id)
        )

        return True

    @staticmethod
    def get_user_permissions(db: Session, user_id: UUID) -> List[str]:
        """
        获取用户的所有权限代码

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            List[str]: 权限代码列表
        """
        # 查询用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # 超级用户拥有所有权限
        if user.is_superuser:
            all_permissions = db.query(Permission).all()
            return [perm.code for perm in all_permissions]

        # 查询用户的角色权限
        permissions = db.query(Permission).join(
            "role_permissions"
        ).join(
            Role, Role.id == RolePermission.role_id
        ).join(
            UserRole, UserRole.role_id == Role.id
        ).filter(
            UserRole.user_id == user_id
        ).distinct().all()

        return [perm.code for perm in permissions]

    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: UUID,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """
        创建审计日志

        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 操作详情
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            AuditLog: 审计日志对象
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(audit_log)
        db.commit()

        return audit_log
