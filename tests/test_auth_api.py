"""认证和权限 API 测试"""
import pytest
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission
from shared.security.password import verify_password, get_password_hash


class TestAuthAPI:
    """认证 API 测试"""

    def test_login_success(self, client: TestClient, db: Session):
        """测试成功登录"""
        # 创建测试用户
        user = User(
            username="testuser",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        db.add(user)
        db.commit()

        # 登录
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client: TestClient, db: Session):
        """测试密码错误"""
        user = User(
            username="testuser",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401

    def test_login_user_not_found(self, client: TestClient):
        """测试用户不存在"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db: Session):
        """测试未激活用户登录"""
        user = User(
            username="inactive",
            hashed_password=get_password_hash("password"),
            is_active=False
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactive", "password": "password"}
        )

        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, db: Session):
        """测试获取当前用户信息"""
        # 创建用户和角色
        role = Role(name="engineer", display_name="工程师", level=40)
        db.add(role)
        db.flush()

        user = User(
            username="testuser",
            hashed_password=get_password_hash("password"),
            full_name="测试用户",
            email="test@example.com",
            is_active=True
        )
        db.add(user)
        db.flush()

        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        db.commit()

        # 登录获取 token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password"}
        )
        token = login_response.json()["access_token"]

        # 获取当前用户信息
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["full_name"] == "测试用户"
        assert data["email"] == "test@example.com"
        assert len(data["roles"]) == 1
        assert data["roles"][0]["name"] == "engineer"

    def test_change_password(self, client: TestClient, db: Session):
        """测试修改密码"""
        user = User(
            username="testuser",
            hashed_password=get_password_hash("oldpassword"),
            is_active=True
        )
        db.add(user)
        db.commit()

        # 登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "oldpassword"}
        )
        token = login_response.json()["access_token"]

        # 修改密码
        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "oldpassword", "new_password": "newpassword123"}
        )

        assert response.status_code == 200

        # 验证新密码
        db.refresh(user)
        assert verify_password("newpassword123", user.hashed_password)

    def test_change_password_wrong_old_password(self, client: TestClient, db: Session):
        """测试修改密码时旧密码错误"""
        user = User(
            username="testuser",
            hashed_password=get_password_hash("oldpassword"),
            is_active=True
        )
        db.add(user)
        db.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "oldpassword"}
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "wrongpassword", "new_password": "newpassword"}
        )

        assert response.status_code == 400


class TestUserManagement:
    """用户管理 API 测试"""

    def test_create_user_as_admin(self, client: TestClient, db: Session):
        """测试管理员创建用户"""
        # 创建管理员
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        db.add(admin)

        # 创建角色
        role = Role(name="engineer", display_name="工程师", level=40)
        db.add(role)
        db.commit()

        # 管理员登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        admin_token = login_response.json()["access_token"]

        # 创建用户
        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "password": "password123",
                "full_name": "新用户",
                "email": "newuser@example.com",
                "role_ids": [str(role.id)]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["full_name"] == "新用户"

    def test_create_user_as_normal_user_forbidden(self, client: TestClient, db: Session):
        """测试普通用户无法创建用户"""
        # 创建普通用户
        user = User(
            username="normaluser",
            hashed_password=get_password_hash("password"),
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()

        # 普通用户登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "normaluser", "password": "password"}
        )
        token = login_response.json()["access_token"]

        # 尝试创建用户
        response = client.post(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "password123"
            }
        )

        assert response.status_code == 403

    def test_list_users_as_admin(self, client: TestClient, db: Session):
        """测试管理员获取用户列表"""
        # 创建管理员和普通用户
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        user1 = User(username="user1", hashed_password=get_password_hash("pass"), is_active=True)
        user2 = User(username="user2", hashed_password=get_password_hash("pass"), is_active=True)
        db.add_all([admin, user1, user2])
        db.commit()

        # 管理员登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        admin_token = login_response.json()["access_token"]

        # 获取用户列表
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_user(self, client: TestClient, db: Session):
        """测试更新用户"""
        # 创建管理员和测试用户
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        user = User(
            username="testuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db.add_all([admin, user])
        db.commit()
        user_id = user.id

        # 管理员登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        admin_token = login_response.json()["access_token"]

        # 更新用户
        response = client.put(
            f"/api/v1/auth/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "full_name": "更新后的用户名",
                "email": "updated@example.com"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "更新后的用户名"

    def test_delete_user(self, client: TestClient, db: Session):
        """测试删除用户"""
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        user = User(
            username="testuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db.add_all([admin, user])
        db.commit()
        user_id = user.id

        # 管理员登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        admin_token = login_response.json()["access_token"]

        # 删除用户
        response = client.delete(
            f"/api/v1/auth/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204

        # 验证用户已删除
        deleted_user = db.query(User).filter(User.id == user_id).first()
        assert deleted_user is None


class TestPermissions:
    """权限测试"""

    def test_superuser_has_all_permissions(self, client: TestClient, db: Session):
        """测试超级用户拥有所有权限"""
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # 超级用户应该能访问所有端点
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_normal_user_no_admin_access(self, client: TestClient, db: Session):
        """测试普通用户无管理员权限"""
        user = User(
            username="normaluser",
            hashed_password=get_password_hash("password"),
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "normaluser", "password": "password"}
        )
        token = login_response.json()["access_token"]

        # 普通用户无法访问用户管理
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
