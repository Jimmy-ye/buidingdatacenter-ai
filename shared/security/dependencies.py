"""FastAPI 依赖注入：认证和权限"""
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from shared.db.session import get_db
from shared.db.models_auth import User, Role, Permission
from shared.security.jwt import verify_token

# HTTP Bearer 认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    token = credentials.credentials

    # 验证 Token
    user_id = verify_token(token, token_type="access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前激活用户（额外的激活检查）

    Args:
        current_user: 当前用户

    Returns:
        User: 当前激活用户

    Raises:
        HTTPException: 用户未激活时抛出 403 错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前超级用户（管理员权限检查）

    Args:
        current_user: 当前用户

    Returns:
        User: 当前超级用户

    Raises:
        HTTPException: 用户不是管理员时抛出 403 错误
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have sufficient privileges"
        )
    return current_user


class PermissionChecker:
    """
    权限检查器（可重用的依赖类）

    使用示例:
        @app.get("/api/v1/projects")
        def get_projects(
            _=Depends(PermissionChecker("projects.read")),
            db: Session = Depends(get_db)
        ):
            ...
    """

    def __init__(self, required_permission: str):
        """
        初始化权限检查器

        Args:
            required_permission: 需要的权限代码（例如: projects.read）
        """
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> bool:
        """
        检查用户是否拥有所需权限

        Args:
            current_user: 当前用户
            db: 数据库会话

        Returns:
            bool: 是否拥有权限

        Raises:
            HTTPException: 权限不足时抛出 403 错误
        """
        # 超级用户拥有所有权限
        if current_user.is_superuser:
            return True

        # 查询用户的所有角色
        user_roles = db.query(Role).join(
            "user_roles"
        ).filter(
            User.id == current_user.id
        ).all()

        # 查询这些角色的所有权限
        permissions = db.query(Permission).join(
            "role_permissions"
        ).join(
            Role
        ).filter(
            Role.id.in_([role.id for role in user_roles])
        ).all()

        # 检查是否拥有所需权限
        permission_codes = {perm.code for perm in permissions}
        if self.required_permission not in permission_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.required_permission} required"
            )

        return True


def require_permissions(*permissions: str):
    """
    需要多个权限中的任意一个（OR 关系）

    使用示例:
        @app.post("/api/v1/projects")
        def create_project(
            _=Depends(require_permissions("projects.create", "projects.admin")),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def check_permissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> bool:
        # 超级用户拥有所有权限
        if current_user.is_superuser:
            return True

        # 查询用户的所有权限
        user_roles = db.query(Role).join(
            "user_roles"
        ).filter(
            User.id == current_user.id
        ).all()

        user_permissions = db.query(Permission).join(
            "role_permissions"
        ).join(
            Role
        ).filter(
            Role.id.in_([role.id for role in user_roles])
        ).all()

        permission_codes = {perm.code for perm in user_permissions}

        # 检查是否拥有所需权限中的任意一个
        if not any(perm in permission_codes for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: one of {permissions} required"
            )

        return True

    return check_permissions
