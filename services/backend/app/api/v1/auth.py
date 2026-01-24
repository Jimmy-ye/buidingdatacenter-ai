"""认证和用户管理 API 路由"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from shared.db.session import get_db
from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission
from shared.security.dependencies import get_current_user, get_current_superuser
from shared.config.settings import get_settings

from ...schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserCreate,
    UserUpdate,
    ChangePasswordRequest,
    UserInfo,
    UserDetail,
    RoleInfo,
    RoleDetail,
    PermissionInfo,
    AuditLogInfo
)
from ...services.auth_service import AuthService

router = APIRouter()
settings = get_settings()


# ===== 认证端点 =====

@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回访问令牌和刷新令牌
    """
    try:
        result = AuthService.login(
            db=db,
            username=request.username,
            password=request.password,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    返回新的访问令牌和刷新令牌
    """
    try:
        result = AuthService.refresh_token(db=db, refresh_token=request.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", summary="用户注销")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户注销（可选实现）

    客户端删除本地 Token 即可，服务端可以实现 Token 黑名单
    """
    AuthService.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="logout"
    )
    return {"message": "Logged out successfully"}


# ===== 当前用户信息 =====

@router.get("/me", response_model=UserDetail, summary="获取当前用户信息")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前登录用户的详细信息"""
    # 查询用户的角色
    user_roles = db.query(Role).join(
        UserRole
    ).filter(
        UserRole.user_id == current_user.id
    ).all()

    # 构建响应
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "level": role.level
            }
            for role in user_roles
        ]
    }

    return user_dict


@router.post("/me/change-password", summary="修改密码")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户密码

    - **old_password**: 旧密码
    - **new_password**: 新密码（至少6位）
    """
    try:
        AuthService.change_password(
            db=db,
            user_id=current_user.id,
            old_password=request.old_password,
            new_password=request.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ===== 用户管理（管理员） =====

@router.get("/users", response_model=List[UserDetail], summary="获取用户列表")
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（仅管理员）

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    """
    users = db.query(User).offset(skip).limit(limit).all()

    result = []
    for user in users:
        # 查询角色
        user_roles = db.query(Role).join(
            UserRole
        ).filter(
            UserRole.user_id == user.id
        ).all()

        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "roles": [
                {
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.display_name,
                    "level": role.level
                }
                for role in user_roles
            ]
        }
        result.append(user_dict)

    return result


@router.get("/users/{user_id}", response_model=UserDetail, summary="获取用户详情")
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取指定用户的详细信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 查询角色
    user_roles = db.query(Role).join(
        UserRole
    ).filter(
        UserRole.user_id == user.id
    ).all()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "level": role.level
            }
            for role in user_roles
        ]
    }


@router.post("/users", response_model=UserInfo, status_code=status.HTTP_201_CREATED, summary="创建用户")
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    创建新用户（仅管理员）

    - **username**: 用户名（唯一，3-50字符）
    - **password**: 密码（至少6位）
    - **email**: 邮箱（可选）
    - **full_name**: 全名（可选）
    - **phone**: 手机号（可选）
    - **role_ids**: 角色ID列表（可选）
    - **is_active**: 是否激活（默认True）
    """
    try:
        user = AuthService.create_user(
            db=db,
            user_data=user_data.dict(),
            creator_id=current_user.id
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{user_id}", response_model=UserInfo, summary="更新用户")
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（仅管理员）

    所有字段都是可选的，只更新提供的字段
    """
    # 过滤 None 值
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    user = AuthService.update_user(
        db=db,
        user_id=user_id,
        user_data=update_data,
        updater_id=current_user.id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    删除用户（仅管理员）

    注意：删除用户会级联删除其角色关系和审计日志
    """
    success = AuthService.delete_user(
        db=db,
        user_id=user_id,
        deleter_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return None


# ===== 角色和权限（管理员） =====

@router.get("/roles", response_model=List[RoleInfo], summary="获取角色列表")
def list_roles(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取所有角色（仅管理员）"""
    roles = db.query(Role).order_by(Role.level.desc()).all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleDetail, summary="获取角色详情")
def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取角色详细信息，包含权限列表（仅管理员）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # 查询权限
    permissions = db.query(Permission).join(
        "role_permissions"
    ).filter(
        RolePermission.role_id == role_id
    ).all()

    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "level": role.level,
        "created_at": role.created_at,
        "permissions": [perm.code for perm in permissions]
    }


@router.get("/permissions", response_model=List[PermissionInfo], summary="获取权限列表")
def list_permissions(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取所有权限（仅管理员）"""
    permissions = db.query(Permission).order_by(Permission.resource, Permission.action).all()
    return permissions


# ===== 审计日志（管理员） =====

@router.get("/audit-logs", response_model=List[AuditLogInfo], summary="获取审计日志")
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取审计日志（仅管理员）

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    """
    logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()

    # 添加用户名（方便查询）
    result = []
    for log in logs:
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            username = user.username if user else None
        else:
            username = None

        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "username": username,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        result.append(log_dict)

    return result
