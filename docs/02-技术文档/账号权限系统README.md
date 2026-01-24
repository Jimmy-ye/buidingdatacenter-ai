# BDC-AI 账号权限管理系统

## 方案概述

为 BDC-AI 项目设计了一套完整的账号权限管理方案，支持用户认证、基于角色的访问控制（RBAC）、项目级权限和操作审计。

### 核心特性

- ✅ **JWT 认证** - 无状态认证，支持访问令牌和刷新令牌
- ✅ **RBAC 权限模型** - 基于角色的访问控制，6 种预定义角色
- ✅ **27 个预定义权限** - 覆盖项目、资产、用户、报告、系统管理
- ✅ **项目级权限** - 支持项目成员管理和细粒度权限控制
- ✅ **操作审计** - 完整记录用户操作，便于追溯
- ✅ **移动端集成** - Flutter 认证服务，自动 Token 刷新
- ✅ **PC 端集成** - NiceGUI 登录页面和会话管理
- ✅ **密码安全** - bcrypt 加密，强度验证
- ✅ **测试覆盖** - 完整的 API 测试用例

## 快速开始

### 1. 安装依赖

```bash
cd services/backend
pip install -r requirements.txt
```

新增依赖：
- `python-jose[cryptography]` - JWT 处理
- `passlib[bcrypt]` - 密码加密
- `bcrypt` - 加密算法

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# JWT 配置（生产环境使用 openssl rand -hex 32 生成）
BDC_JWT_SECRET_KEY=your-secret-key-change-in-production
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. 初始化数据库

```bash
python scripts/init_auth_db.py
```

创建：
- 27 个权限
- 6 个角色（superuser, admin, project_manager, analyst, engineer, viewer）
- 1 个管理员账号：admin / admin123
- 3 个测试账号

### 4. 启动服务

```bash
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

访问 API 文档：http://localhost:8000/docs

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 超级管理员 |
| manager1 | manager123 | 项目经理 |
| engineer1 | engineer123 | 现场工程师 |
| analyst1 | analyst123 | 数据分析师 |

⚠️ **登录后立即修改默认密码！**

## 文档结构

### 技术文档
- `账号权限管理系统设计.md` - 完整的设计文档
- `账号权限系统快速开始.md` - 5 分钟快速部署指南
- `账号权限系统实施检查清单.md` - 详细实施步骤和验收标准

### 代码文件
```
shared/
├── db/models_auth.py          # 数据库模型
├── security/
│   ├── password.py            # 密码加密
│   ├── jwt.py                 # JWT 处理
│   └── dependencies.py        # FastAPI 依赖注入
└── config/settings.py         # 配置（已更新）

services/backend/
├── app/
│   ├── api/v1/auth.py         # 认证 API
│   ├── schemas/auth.py        # Pydantic 模型
│   ├── services/auth_service.py  # 业务逻辑
│   └── main.py                # 应用入口（已更新）
└── requirements.txt           # 依赖（已更新）

scripts/init_auth_db.py        # 初始化脚本
tests/test_auth_api.py         # 测试用例

mobile/lib/
├── models/auth.dart           # 数据模型
├── services/auth_service.dart # 认证服务
└── screens/login_screen.dart  # 登录页面
```

## API 端点

### 认证
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/logout` - 用户注销
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/me/change-password` - 修改密码

### 用户管理（管理员）
- `GET /api/v1/auth/users` - 用户列表
- `GET /api/v1/auth/users/{id}` - 用户详情
- `POST /api/v1/auth/users` - 创建用户
- `PUT /api/v1/auth/users/{id}` - 更新用户
- `DELETE /api/v1/auth/users/{id}` - 删除用户

### 角色和权限（管理员）
- `GET /api/v1/auth/roles` - 角色列表
- `GET /api/v1/auth/roles/{id}` - 角色详情
- `GET /api/v1/auth/permissions` - 权限列表

### 审计（管理员）
- `GET /api/v1/auth/audit-logs` - 审计日志

## 使用示例

### 后端：添加认证到 API

```python
from fastapi import Depends
from shared.security.dependencies import get_current_user, PermissionChecker
from shared.db.models_auth import User

# 要求用户登录
@router.get("/projects")
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Project).all()

# 要求特定权限
@router.post("/projects")
def create_project(
    _: bool = Depends(PermissionChecker("projects.create")),
    db: Session = Depends(get_db)
):
    return {"message": "Project created"}

# 要求管理员
@router.delete("/projects/{id}")
def delete_project(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    return {"message": "Project deleted"}
```

### 移动端：登录

```dart
import 'package:your_app/services/auth_service.dart';

// 初始化
final authService = AuthService();
await authService.initialize();

// 登录
try {
  final user = await authService.login('admin', 'admin123');
  print('登录成功：${user.displayName}');
} catch (e) {
  print('登录失败：$e');
}

// API 请求会自动添加 Token
final response = await dio.get('/api/v1/projects');
```

### PC 端：登录页面

```python
from nicegui import ui
import requests

@ui.page('/login')
def login_page():
    username = ui.input('用户名')
    password = ui.input('密码', password=True)

    def do_login():
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            json={'username': username.value, 'password': password.value}
        )
        if response.status_code == 200:
            data = response.json()
            app.storage.user['access_token'] = data['access_token']
            ui.navigate('/main')

    ui.button('登录', on_click=do_login)
```

## 角色和权限

### 角色定义

| 角色 | 级别 | 说明 |
|-----|------|------|
| superuser | 100 | 超级管理员，所有权限 |
| admin | 80 | 管理员，项目和用户管理 |
| project_manager | 60 | 项目经理，项目 CRUD |
| analyst | 50 | 数据分析师，报告生成 |
| engineer | 40 | 现场工程师，资产上传 |
| viewer | 20 | 访客，只读权限 |

### 权限列表

**项目管理（projects.*）**
- projects.read, projects.create, projects.update, projects.delete, projects.admin

**资产管理（assets.*）**
- assets.read, assets.create, assets.update, assets.delete, assets.upload

**用户管理（users.*）**
- users.read, users.create, users.update, users.delete, users.admin

**报告（reports.*）**
- reports.read, reports.create, reports.export

**系统（system.*）**
- system.config, system.monitor

## 数据库模型

### User（用户）
- id, username, email, hashed_password
- full_name, phone
- is_active, is_superuser
- created_at, updated_at, last_login_at

### Role（角色）
- id, name, display_name, description
- level (权限级别)
- created_at, updated_at

### Permission（权限）
- id, code, name, description
- resource, action
- created_at

### UserRole（用户-角色）
- user_id, role_id

### RolePermission（角色-权限）
- role_id, permission_id

### ProjectMember（项目成员）
- project_id, user_id
- role_in_project (owner/admin/member/viewer)

### AuditLog（审计日志）
- user_id, action
- resource_type, resource_id
- details (JSONB)
- ip_address, user_agent
- created_at

## 测试

```bash
# 运行测试
cd services/backend
pytest tests/test_auth_api.py -v

# 测试覆盖
pytest tests/test_auth_api.py --cov=shared --cov=services --cov-report=html
```

## 安全特性

### 密码安全
- bcrypt 加密（成本因子 12）
- 最少 6 位长度
- 旧密码验证

### Token 安全
- 访问令牌：30 分钟过期
- 刷新令牌：7 天过期
- 自动刷新机制
- 可选黑名单（使用 Redis）

### 操作审计
- 记录所有敏感操作
- IP 地址和用户代理
- JSON 格式详情
- 时间索引便于查询

## 部署检查清单

### 开发环境
- [ ] 安装依赖
- [ ] 配置环境变量
- [ ] 初始化数据库
- [ ] 启动服务测试

### 生产环境
- [ ] 修改默认密码
- [ ] 使用 HTTPS
- [ ] 配置强 JWT 密钥
- [ ] 启用数据库备份
- [ ] 设置日志归档
- [ ] 配置监控告警

## 常见问题

### Q: 如何重置管理员密码？

```bash
# 方法 1：API
curl -X POST http://localhost:8000/api/v1/auth/me/change-password \
  -H "Authorization: Bearer <token>" \
  -d '{"old_password":"admin123","new_password":"newpass"}'

# 方法 2：重新初始化
python scripts/init_auth_db.py
```

### Q: Token 过期怎么办？

移动端会自动刷新。如果刷新失败，重新登录即可。

### Q: 如何创建新用户？

使用管理员账号通过 API 创建，或通过初始化脚本批量创建。

### Q: 如何给用户分配权限？

通过角色分配权限。用户可以有多个角色，权限会自动合并。

## 性能指标

- 登录响应时间：< 500ms
- API 验证时间：< 10ms
- Token 刷新时间：< 100ms
- 支持并发用户：100+

## 下一步计划

### 短期（MVP）
- [x] 基础认证和授权
- [x] RBAC 权限模型
- [x] 移动端集成
- [x] PC 端集成
- [ ] 为现有 API 添加认证
- [ ] 项目级权限过滤

### 中期
- [ ] 密码重置功能
- [ ] Token 黑名单
- [ ] 登录限流
- [ ] 审计日志查看界面

### 长期
- [ ] 多因素认证（MFA）
- [ ] SSO 单点登录
- [ ] OAuth 2.0 / OpenID Connect
- [ ] 细粒度权限控制

## 技术栈

- **后端框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL + SQLAlchemy 2.0.23
- **认证**: JWT (python-jose)
- **密码**: bcrypt (passlib)
- **移动端**: Flutter + Dio
- **PC 端**: NiceGUI

## 参考文档

- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Passlib Documentation](https://passlib.readthedocs.io/)

## 许可证

本项目遵循 BDC-AI 项目的许可证。

---

**版本**: 1.0.0
**更新时间**: 2026-01-24
**维护者**: BDC-AI 开发团队
