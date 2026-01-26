"""认证相关的 Pydantic 模型"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ===== 请求模型 =====

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class UserCreate(BaseModel):
    """创建用户请求（管理员）"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    role_ids: List[UUID] = Field(default_factory=list, description="角色ID列表")
    is_active: bool = Field(True, description="是否激活")


class UserUpdate(BaseModel):
    """更新用户请求（管理员）"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role_ids: Optional[List[UUID]] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


# ===== 响应模型 =====

class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="Token 类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserInfo(BaseModel):
    """用户基本信息"""
    id: UUID
    username: str
    email: Optional[str]
    full_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class PermissionInfoSimple(BaseModel):
    """权限信息（简化版）"""
    code: str
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class UserRoleInfo(BaseModel):
    """用户角色信息"""
    id: UUID
    name: str
    display_name: str
    level: int

    class Config:
        from_attributes = True


class UserRoleInfoWithPermissions(UserRoleInfo):
    """用户角色信息（包含权限）"""
    permissions: List[PermissionInfoSimple] = Field(default_factory=list, description="角色权限列表")


class UserDetail(UserInfo):
    """用户详细信息"""
    roles: List[UserRoleInfo] = Field(default_factory=list, description="用户角色列表")

    class Config:
        from_attributes = True


class UserDetailWithPermissions(UserInfo):
    """用户详细信息（包含权限）"""
    roles: List[UserRoleInfoWithPermissions] = Field(default_factory=list, description="用户角色列表（含权限）")

    class Config:
        from_attributes = True


class RoleInfo(BaseModel):
    """角色信息"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    level: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoleDetail(RoleInfo):
    """角色详细信息（包含权限）"""
    permissions: List[str] = Field(default_factory=list, description="权限代码列表")


class PermissionInfo(BaseModel):
    """权限信息"""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    resource: str
    action: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogInfo(BaseModel):
    """审计日志信息"""
    id: UUID
    user_id: Optional[UUID]
    username: Optional[str] = Field(None, description="用户名（冗余字段，方便查询）")
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
