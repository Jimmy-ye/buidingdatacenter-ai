"""账号和权限管理相关的数据库模型"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Text, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)

    # 状态字段
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # 关系
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    project_members = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan",
                                  foreign_keys="ProjectMember.user_id")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Integer, default=0, nullable=False)  # 角色级别，数字越大权限越高

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, display_name={self.display_name})>"


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)  # 例如: projects.create, assets.delete
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  # 资源类型: projects, assets, users, etc.
    action = Column(String(50), nullable=False)  # 操作: create, read, update, delete, etc.

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permission(id={self.id}, code={self.code})>"


class UserRole(Base):
    """用户-角色关联表"""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    # 唯一约束确保一个用户不能重复拥有同一角色
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        {"schema": None},
    )


class RolePermission(Base):
    """角色-权限关联表"""
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class ProjectMember(Base):
    """项目成员关系表（项目级权限）"""
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_in_project = Column(String(50), nullable=False, default="member")  # 项目中的角色: owner, admin, member, viewer

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 关系
    user = relationship("User", back_populates="project_members", foreign_keys=[user_id])

    # 唯一约束确保一个用户在一个项目中只有一个角色
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
        {"schema": None},
    )


class AuditLog(Base):
    """操作审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # 操作类型: login, create, update, delete, etc.
    resource_type = Column(String(50), nullable=True)  # 资源类型: project, asset, user, etc.
    resource_id = Column(String(100), nullable=True)  # 资源ID
    details = Column(JSONB, nullable=True)  # 操作详情（JSON格式）

    # 请求信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
