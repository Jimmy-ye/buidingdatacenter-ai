# BDC-AI 后端 API 开发指南

---
**标题**: 后端 API 开发指南
**最后更新**: 2026-01-25
**适用对象**: 后端开发者
**难度等级**: ⭐⭐⭐
**预计阅读时间**: 25 分钟
---

## 📋 目录

1. [概述](#1-概述)
2. [快速开始](#2-快速开始)
3. [认证机制](#3-认证机制)
4. [核心 API 端点](#4-核心-api-端点)
5. [数据库操作](#5-数据库操作)
6. [错误处理](#6-错误处理)
7. [开发最佳实践](#7-开发最佳实践)
8. [常见问题](#8-常见问题)
9. [附录](#9-附录)

---

## 1. 概述

### 1.1 技术栈

BDC-AI 后端基于以下技术栈构建：

- **Web 框架**: FastAPI 0.104.1
  - 高性能异步框架
  - 自动生成 OpenAPI 文档
  - 类型验证（Pydantic）

- **数据库 ORM**: SQLAlchemy 2.0.23
  - Python SQL 工具包和 ORM
  - 支持 asyncio
  - 声明式模型定义

- **数据库**: PostgreSQL 18.1
  - 关系型数据库
  - 支持 UUID、JSONB 类型
  - 时序数据扩展（TimescaleDB）

- **认证**: JWT (python-jose[cryptography])
  - 无状态认证
  - 访问令牌 + 刷新令牌

### 1.2 目录结构

```
services/backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # 认证 API
│   │       ├── projects.py     # 项目管理 API
│   │       ├── assets.py       # 资产管理 API
│   │       ├── engineering.py  # 工程结构 API
│   │       └── health.py       # 健康检查
│   ├── schemas/
│   │   ├── project.py          # 项目 Pydantic 模型
│   │   ├── asset.py            # 资产 Pydantic 模型
│   │   └── engineering.py      # 工程结构 Pydantic 模型
│   ├── services/
│   │   ├── tree_service.py     # 树结构服务
│   │   └── image_pipeline.py   # 图片处理管道
│   └── core/
│       └── config.py           # 核心配置（待添加）
└── requirements.txt            # Python 依赖
```

### 1.3 API 设计原则

BDC-AI 遵循以下 API 设计原则：

- ✅ **RESTful 风格**: 资源导向的 URL 设计
- ✅ **版本管理**: 所有 API 位于 `/api/v1/` 下
- ✅ **统一响应**: 使用 Pydantic 模型确保响应一致性
- ✅ **错误处理**: 标准化的错误响应格式
- ✅ **文档优先**: 自动生成 OpenAPI 文档

---

## 2. 快速开始

### 2.1 环境搭建

#### 安装依赖

```bash
cd services/backend
pip install -r requirements.txt
```

主要依赖：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL 驱动
- `python-jose` - JWT 处理
- `passlib` - 密码加密
- `pydantic` - 数据验证
- `python-multipart` - 文件上传

#### 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 数据库连接
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# JWT 密钥（生产环境使用 openssl rand -hex 32 生成）
BDC_JWT_SECRET_KEY=your-secret-key-change-in-production
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7

# GLM API Key（用于 AI 分析）
GLM_API_KEY=your_glm_api_key_here

# MinIO 对象存储（可选）
BDC_MINIO_ENDPOINT=localhost:9000
BDC_MINIO_ACCESS_KEY=minioadmin
BDC_MINIO_SECRET_KEY=minioadmin
```

### 2.2 启动开发服务器

```bash
# 从项目根目录启动
python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload

# 或从 backend 目录启动
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

启动成功后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2.3 测试 API

#### 健康检查（无需认证）

```bash
curl http://localhost:8000/api/v1/health
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T10:00:00Z"
}
```

#### 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

响应：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "username": "admin",
    "email": "admin@example.com",
    "role": "superuser"
  }
}
```

#### 使用 Token 访问受保护的 API

```bash
# 获取项目列表
curl http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer <your_access_token>"
```

---

## 3. 认证机制

### 3.1 JWT Token 认证

BDC-AI 使用 JWT（JSON Web Token）进行无状态认证。

#### Token 类型

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| Access Token | 30 分钟 | 访问受保护的 API |
| Refresh Token | 7 天 | 刷新 Access Token |

#### Token 获取流程

```
1. 用户登录（POST /api/v1/auth/login）
   ↓
2. 验证用户名和密码
   ↓
3. 生成 Access Token 和 Refresh Token
   ↓
4. 返回 Token 给客户端
   ↓
5. 客户端在请求头中携带 Token
   Authorization: Bearer <access_token>
   ↓
6. 后端验证 Token 并处理请求
```

### 3.2 依赖注入使用

FastAPI 使用依赖注入系统进行认证。

#### 获取当前用户

```python
from fastapi import Depends
from shared.db.models_auth import User
from shared.security.dependencies import get_current_user

@router.get("/api/v1/projects/")
async def list_projects(
    current_user: User = Depends(get_current_user)
):
    """当前登录用户自动注入到 current_user 参数"""
    return {"user": current_user.username}
```

#### 可选认证（允许匿名访问）

```python
from fastapi import Depends
from shared.security.dependencies import get_current_user_optional
from typing import Optional

@router.get("/api/v1/public/projects")
async def list_public_projects(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """允许匿名访问，但如果提供了 Token 也会验证"""
    if current_user:
        return {"message": f"Hello {current_user.username}"}
    else:
        return {"message": "Hello anonymous"}
```

### 3.3 权限检查

#### 基于角色的权限检查

```python
from shared.security.dependencies import require_permission

@router.delete("/api/v1/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_permission("projects.delete"))
):
    """只有拥有 projects.delete 权限的用户才能访问"""
    # 删除项目逻辑
    pass
```

#### 多权限检查（OR 逻辑）

```python
@router.patch("/api/v1/projects/{project_id}")
async def update_project(
    project_id: str,
    current_user: User = Depends(
        require_permission_any("projects.update", "projects.admin")
    )
):
    """拥有 projects.update 或 projects.admin 任一权限即可"""
    # 更新项目逻辑
    pass
```

---

## 4. 核心 API 端点

### 4.1 项目管理 API

#### 查询项目列表

**端点**: `GET /api/v1/projects/`

**认证**: 需要登录

**查询参数**:
- `status`: 项目状态过滤（如 `in_progress`、`completed`）
- `type`: 项目类型过滤（如 `commercial`、`industrial`）
- `client_contains`: 客户名称模糊搜索
- `name_contains`: 项目名称模糊搜索
- `include_deleted`: 是否包含已删除项目（默认 `false`）

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/projects/?status=in_progress&client_contains=科技" \
  -H "Authorization: Bearer <token>"
```

**响应示例**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "某科技公司总部节能改造",
    "client": "某科技公司",
    "location": "北京市朝阳区",
    "type": "commercial",
    "status": "in_progress",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-25T10:00:00Z",
    "is_deleted": false
  }
]
```

#### 创建项目

**端点**: `POST /api/v1/projects/`

**认证**: 需要 `projects.create` 权限

**请求体**:
```json
{
  "name": "新项目",
  "client": "客户A",
  "location": "上海市",
  "type": "commercial",
  "status": "planning",
  "description": "项目描述"
}
```

**字段说明**:
- `name`: 项目名称（必填）
- `client`: 客户名称（必填）
- `location`: 项目位置（可选）
- `type`: 项目类型（必填，可选值：`commercial`、`industrial`、`public_building`、`datacenter`、`mixed_use`）
- `status`: 项目状态（必填，可选值：`planning`、`in_progress`、`completed`、`on_hold`）
- `description`: 项目描述（可选）

**响应示例**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "新项目",
  "client": "客户A",
  "location": "上海市",
  "type": "commercial",
  "status": "planning",
  "description": "项目描述",
  "created_at": "2026-01-25T10:30:00Z",
  "updated_at": "2026-01-25T10:30:00Z",
  "is_deleted": false
}
```

#### 更新项目

**端点**: `PATCH /api/v1/projects/{project_id}`

**认证**: 需要 `projects.update` 权限

**请求体**:
```json
{
  "name": "更新后的项目名称",
  "status": "in_progress"
}
```

**注意**: 只需提供要更新的字段，未提供的字段保持不变。

#### 删除项目（软删除）

**端点**: `DELETE /api/v1/projects/{project_id}`

**认证**: 需要 `projects.delete` 权限

**说明**: 这是软删除，项目不会真正从数据库删除，而是标记 `is_deleted=true`。

---

### 4.2 资产管理 API

#### 上传图片资产

**端点**: `POST /api/v1/assets/upload_image_with_note`

**认证**: 需要 `assets.upload` 权限

**请求类型**: `multipart/form-data`

**表单字段**:
- `file`: 图片文件（必填）
- `project_id`: 项目 UUID（必填）
- `device_id`: 设备 UUID（可选）
- `building_id`: 建筑 UUID（可选）
- `zone_id`: 区域 UUID（可选）
- `system_id`: 系统 UUID（可选）
- `content_role`: 内容角色（可选，如 `scene_issue`、`nameplate`）
- `note`: 文字备注（可选）

**示例请求**:
```bash
curl -X POST http://localhost:8000/api/v1/assets/upload_image_with_note \
  -H "Authorization: Bearer <token>" \
  -F "file=@photo.jpg" \
  -F "project_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "device_id=device-uuid" \
  -F "content_role=scene_issue" \
  -F "note=5F西风机盘管异响"
```

**响应示例**:
```json
{
  "id": "asset-uuid",
  "project_id": "...",
  "building_id": "...",
  "zone_id": "...",
  "system_id": "...",
  "device_id": "...",
  "engineer_path": "A座办公楼 / HVAC系统 / 风机盘管FCU-03",
  "modality": "image",
  "title": null,
  "description": "5F西风机盘管异响",
  "created_at": "2026-01-25T10:30:00Z"
}
```

#### 查询资产列表

**端点**: `GET /api/v1/assets/`

**认证**: 需要登录

**查询参数**:
- `project_id`: 项目 UUID（必填）
- `modality`: 模态类型（如 `image`、`table`、`text`）
- `device_id`: 设备 UUID（可选）
- `system_id`: 系统 UUID（可选）
- `limit`: 返回数量限制（默认 20）

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/assets/?project_id=...&modality=image&limit=10" \
  -H "Authorization: Bearer <token>"
```

#### 获取资产详情

**端点**: `GET /api/v1/assets/{asset_id}`

**认证**: 需要登录

**响应示例**:
```json
{
  "id": "asset-uuid",
  "project_id": "...",
  "building_id": "...",
  "zone_id": "...",
  "system_id": "...",
  "device_id": "...",
  "engineer_path": "A座办公楼 / HVAC系统 / 风机盘管FCU-03",
  "location_path": "A座办公楼 / 5F办公区",
  "modality": "image",
  "title": "现场照片",
  "description": "5F西风机盘管异响",
  "created_at": "2026-01-25T10:30:00Z",
  "raw_url": "https://minio.example.com/bucket/path.jpg",
  "structured_payload": {
    "schema_type": "image_annotation",
    "ocr_text": "设备铭牌：FCU-03...",
    "detected_objects": ["fcu", "pipe"],
    "global_tags": ["hvac", "fan_coil_unit"]
  }
}
```

---

### 4.3 工程结构 API

#### 创建建筑

**端点**: `POST /api/v1/projects/{project_id}/buildings`

**认证**: 需要登录

**请求体**:
```json
{
  "name": "A座办公楼",
  "usage_type": "office",
  "floor_area": 15000.0,
  "year_built": 2010,
  "energy_grade": "three_star",
  "tags": ["总部", "主楼"]
}
```

**说明**: 创建建筑后，系统会自动创建 9 个默认系统模板（围护结构、制冷、制热、空调末端、照明、电梯、动力、电力监控、能管平台）。

#### 创建系统

**端点**: `POST /api/v1/buildings/{building_id}/systems`

**认证**: 需要登录

**请求体**:
```json
{
  "type": "HVAC",
  "name": "空调系统1#",
  "description": "主楼空调系统",
  "tags": ["主系统", "高能耗"]
}
```

#### 创建设备

**端点**: `POST /api/v1/systems/{system_id}/devices`

**认证**: 需要登录

**请求体**:
```json
{
  "zone_id": "zone-uuid",  // 可选，指定设备位置
  "device_type": "fcu",
  "model": "风机盘管FCU-03",
  "rated_power": 1.5,
  "serial_no": "FCU-2024-001",
  "tags": ["高能耗", "待维修"]
}
```

**重要**: 设备必须归属于某个系统（`system_id` 从路由获取），可以位于某个区域（`zone_id` 可选）。

#### 获取工程结构树

**端点**: `GET /api/v1/projects/{project_id}/structure_tree`

**认证**: 需要登录

**响应示例**:
```json
{
  "project_id": "...",
  "tree": {
    "id": "project-root",
    "name": "项目根",
    "type": "project_root",
    "children": [
      {
        "id": "building-uuid",
        "name": "A座办公楼",
        "type": "building",
        "usage_type": "office",
        "children": [
          {
            "id": "system-uuid",
            "name": "HVAC系统",
            "type": "system",
            "system_type": "HVAC",
            "children": [
              {
                "id": "device-uuid",
                "name": "风机盘管FCU-03",
                "type": "device",
                "device_type": "fcu",
                "zone": {
                  "id": "zone-uuid",
                  "name": "5F办公区"
                },
                "asset_count": 3
              }
            ]
          }
        ],
        "zones": [
          {
            "id": "zone-uuid",
            "name": "5F办公区",
            "type": "zone",
            "device_count": 15
          }
        ]
      }
    ]
  }
}
```

#### 扁平化查询设备

**端点**: `GET /api/v1/projects/{project_id}/devices/flat`

**认证**: 需要登录

**查询参数**:
- `system_id`: 系统过滤（可选）
- `zone_id`: 区域过滤（可选）
- `device_type`: 设备类型（可选）
- `min_rated_power`: 最小额定功率（可选）
- `tags`: 标签筛选（逗号分隔，AND 逻辑）
- `search`: 全文搜索（可选）

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/projects/.../devices/flat?tags=高能耗,待维修&device_type=fcu" \
  -H "Authorization: Bearer <token>"
```

---

## 5. 数据库操作

### 5.1 SQLAlchemy 使用

BDC-AI 使用 SQLAlchemy 2.0 作为 ORM。

#### 声明式基类

所有模型继承自 `Base`：

```python
from shared.db.base import Base
from sqlalchemy import Column, Integer, String, Float
import uuid

class Building(Base):
    __tablename__ = "buildings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    usage_type = Column(String(50))
    floor_area = Column(Float)
    # ...
```

#### 数据库会话

使用依赖注入获取会话：

```python
from fastapi import Depends
from shared.db.session import get_db
from sqlalchemy.orm import Session

@router.get("/api/v1/projects/{project_id}/buildings")
async def list_buildings(
    project_id: str,
    db: Session = Depends(get_db)
):
    """db 会话自动注入，无需手动创建"""
    buildings = db.query(Building).filter_by(project_id=project_id).all()
    return buildings
```

#### 基本查询

```python
# 查询所有
buildings = db.query(Building).all()

# 条件查询
buildings = db.query(Building).filter_by(project_id=project_id).all()

# 模糊查询
buildings = db.query(Building).filter(
    Building.name.ilike(f"%{keyword}%")
).all()

# 排序
buildings = db.query(Building).order_by(Building.name).all()

# 限制数量
buildings = db.query(Building).limit(10).all()

# 获取单个
building = db.query(Building).filter_by(id=building_id).one_or_none()
```

#### 关系查询

```python
from sqlalchemy.orm import joinedload

# 预加载关联数据（避免 N+1 查询）
buildings = db.query(Building)\
    .options(
        joinedload(Building.systems)
        .joinedload(BuildingSystem.devices)
        .joinedload(Device.zone)
    )\
    .filter_by(project_id=project_id)\
    .all()
```

#### 创建记录

```python
# 创建单个
building = Building(
    project_id=project_id,
    name="A座办公楼",
    usage_type="office"
)
db.add(building)
db.commit()
db.refresh(building)

# 批量创建
db.add_all([
    Building(name="A座", project_id=project_id),
    Building(name="B座", project_id=project_id)
])
db.commit()
```

#### 更新记录

```python
# 查询后更新
building = db.query(Building).filter_by(id=building_id).one()
building.name = "更新后的名称"
db.commit()

# 批量更新
db.query(Building)\
    .filter_by(project_id=project_id)\
    .update({"usage_type": "commercial"})
db.commit()
```

#### 删除记录

```python
# 物理删除
building = db.query(Building).filter_by(id=building_id).one()
db.delete(building)
db.commit()

# 软删除（推荐）
building.is_deleted = True
db.commit()
```

### 5.2 事务处理

```python
from sqlalchemy.exc import IntegrityError

@router.post("/api/v1/projects/{project_id}/buildings")
async def create_building(
    project_id: str,
    payload: BuildingCreate,
    db: Session = Depends(get_db)
):
    try:
        # 开始事务
        building = Building(project_id=project_id, **payload.model_dump())
        db.add(building)
        db.flush()  # 获取 ID 但不提交

        # 创建关联系统
        for system_data in default_systems:
            system = BuildingSystem(
                building_id=building.id,
                **system_data
            )
            db.add(system)

        # 提交整个事务
        db.commit()
        db.refresh(building)

        return building

    except IntegrityError as e:
        # 回滚事务
        db.rollback()
        raise HTTPException(status_code=400, detail="数据冲突")
    except Exception as e:
        # 回滚事务
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. 错误处理

### 6.1 异常类型

BDC-AI 使用标准 HTTP 状态码和错误响应格式。

#### 常用状态码

| 状态码 | 含义 | 使用场景 |
|-------|------|---------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或 Token 无效 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

### 6.2 错误响应格式

#### 标准错误响应

```json
{
  "detail": "错误描述信息"
}
```

#### 验证错误响应（422）

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 6.3 自定义异常

```python
from fastapi import HTTPException, status

# 资源不存在
if project is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found"
    )

# 权限不足
if not has_permission:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to perform this action"
    )

# 业务逻辑错误
if quantity < 0:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Quantity cannot be negative"
    )
```

### 6.4 全局异常处理

```python
# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
```

---

## 7. 开发最佳实践

### 7.1 API 版本管理

所有 API 路由都应在 `/api/v1/` 下：

```python
# app/api/v1/projects.py

router = APIRouter()

@router.get("/")  # 实际路径: /api/v1/projects/
async def list_projects():
    pass
```

在 `app/main.py` 中注册时添加 prefix：

```python
from app.api.v1 import projects

app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["projects"]
)
```

### 7.2 文档生成

FastAPI 自动生成 OpenAPI 文档。

#### 添加文档字符串

```python
@router.get(
    "/",
    response_model=List[ProjectRead],
    summary="List all projects",
    description="Get all projects with optional filters"
)
async def list_projects(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by project status"
    )
):
    """
    List all projects with optional filters.

    Supports filtering by:
    - status: project status (e.g., 'in_progress', 'completed')
    - type: project type (e.g., 'industrial', 'commercial')
    - client: partial match on client name
    - name: partial match on project name

    Returns a list of projects ordered by creation date (newest first).
    """
    pass
```

#### 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 7.3 测试编写

```python
# tests/test_api_projects.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_projects_unauthorized():
    """测试未认证访问"""
    response = client.get("/api/v1/projects/")
    assert response.status_code == 401

def test_list_projects_authorized(auth_token):
    """测试已认证访问"""
    response = client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_project(auth_token):
    """测试创建项目"""
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Test Project",
            "client": "Test Client",
            "type": "commercial",
            "status": "planning"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data
```

### 7.4 性能优化

#### 使用 joinedload 避免 N+1 查询

```python
from sqlalchemy.orm import joinedload

# ❌ 不推荐（N+1 查询）
buildings = db.query(Building).all()
for building in buildings:
    for system in building.systems:  # N+1 查询
        print(system.name)

# ✅ 推荐（使用 joinedload）
buildings = db.query(Building)\
    .options(joinedload(Building.systems))\
    .all()
for building in buildings:
    for system in building.systems:  # 不会产生额外查询
        print(system.name)
```

#### 使用索引

在模型中添加索引：

```python
class Building(Base):
    __tablename__ = "buildings"

    name = Column(String(200), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), index=True)
    usage_type = Column(String(50), index=True)
```

或在数据库中手动创建：

```sql
CREATE INDEX idx_building_project ON buildings(project_id);
CREATE INDEX idx_building_usage_type ON buildings(usage_type);
```

---

## 8. 常见问题

### 8.1 CORS 问题

**问题**: 浏览器报错 "CORS policy: No 'Access-Control-Allow-Origin' header"

**解决方案**:

```python
# app/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.2 认证失败

**问题**: 返回 401 Unauthorized

**可能原因**:
1. Token 未提供
2. Token 格式错误（应为 `Bearer <token>`）
3. Token 已过期
4. JWT 密钥不匹配

**解决方案**:
```bash
# 检查 Token 是否正确设置
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/projects/

# 重新登录获取新 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 8.3 数据库连接失败

**问题**: `sqlalchemy.exc.OperationalError: could not connect to server`

**解决方案**:
1. 检查 PostgreSQL 服务是否运行
   ```bash
   # Windows
   sc query postgresql-x64-18

   # macOS/Linux
   sudo systemctl status postgresql
   ```

2. 检查 `.env` 中的数据库 URL 是否正确
   ```bash
   BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai
   ```

3. 确认数据库已创建
   ```bash
   psql -U postgres -l
   ```

### 8.4 性能问题

**问题**: API 响应缓慢

**排查步骤**:
1. 开启 SQL 日志
   ```python
   # shared/db/session.py
   engine.echo = True  # 开发环境
   ```

2. 检查是否有 N+1 查询
3. 使用 joinedload 预加载关联数据
4. 添加数据库索引
5. 考虑使用分页

---

## 9. 附录

### 9.1 完整 API 列表

#### 认证 API (`/api/v1/auth/`)
- `POST /login` - 用户登录
- `POST /register` - 用户注册
- `GET /me` - 获取当前用户信息
- `POST /me/change-password` - 修改当前用户密码
- `POST /refresh` - 刷新 Token
- `GET /users/` - 获取用户列表
- `POST /users/` - 创建用户
- `GET /users/{user_id}` - 获取用户详情
- `PATCH /users/{user_id}` - 更新用户
- `DELETE /users/{user_id}` - 删除用户
- `GET /roles/` - 获取角色列表
- `GET /permissions/` - 获取权限列表

#### 项目管理 API (`/api/v1/projects/`)
- `GET /` - 获取项目列表
- `POST /` - 创建项目
- `GET /{project_id}` - 获取项目详情
- `PATCH /{project_id}` - 更新项目
- `DELETE /{project_id}` - 删除项目（软删除）

#### 工程结构 API
- `GET /projects/{project_id}/buildings` - 获取建筑列表
- `POST /projects/{project_id}/buildings` - 创建建筑
- `GET /buildings/{building_id}` - 获取建筑详情
- `PATCH /buildings/{building_id}` - 更新建筑
- `DELETE /buildings/{building_id}` - 删除建筑

- `GET /buildings/{building_id}/zones` - 获取区域列表
- `POST /buildings/{building_id}/zones` - 创建区域
- `GET /zones/{zone_id}` - 获取区域详情
- `PATCH /zones/{zone_id}` - 更新区域
- `DELETE /zones/{zone_id}` - 删除区域

- `GET /buildings/{building_id}/systems` - 获取系统列表
- `POST /buildings/{building_id}/systems` - 创建系统
- `GET /systems/{system_id}` - 获取系统详情
- `PATCH /systems/{system_id}` - 更新系统
- `DELETE /systems/{system_id}` - 删除系统

- `GET /systems/{system_id}/devices` - 获取设备列表
- `POST /systems/{system_id}/devices` - 创建设备
- `GET /devices/{device_id}` - 获取设备详情
- `PATCH /devices/{device_id}` - 更新设备
- `DELETE /devices/{device_id}` - 删除设备

- `GET /projects/{project_id}/structure_tree` - 获取工程结构树
- `GET /projects/{project_id}/devices/flat` - 扁平化查询设备

#### 资产管理 API (`/api/v1/assets/`)
- `GET /` - 获取资产列表
- `POST /upload_image_with_note` - 上传图片资产
- `GET /{asset_id}` - 获取资产详情
- `DELETE /{asset_id}` - 删除资产

### 9.2 状态码说明

| 状态码 | 含义 | 使用场景 |
|-------|------|---------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或 Token 无效 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

### 9.3 数据模型定义

#### Project（项目）

```python
{
  "id": "uuid",
  "name": "string",
  "client": "string",
  "location": "string | null",
  "type": "string",  // commercial, industrial, public_building, datacenter, mixed_use
  "status": "string",  // planning, in_progress, completed, on_hold
  "description": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_deleted": "boolean"
}
```

#### Building（建筑）

```python
{
  "id": "uuid",
  "project_id": "uuid",
  "name": "string",
  "usage_type": "string | null",  // office, commercial, datacenter, mixed_use
  "floor_area": "float | null",
  "gfa_area": "float | null",
  "year_built": "integer | null",
  "energy_grade": "string | null",  // five_star, four_star, three_star
  "tags": ["string"] | null
}
```

#### Asset（资产）

```python
{
  "id": "uuid",
  "project_id": "uuid",
  "building_id": "uuid | null",
  "zone_id": "uuid | null",
  "system_id": "uuid | null",
  "device_id": "uuid | null",
  "engineer_path": "string | null",  // "A座办公楼 / HVAC系统 / 风机盘管FCU-03"
  "location_path": "string | null",  // "A座办公楼 / 5F办公区"
  "modality": "string",  // image, table, text, audio, document, timeseries_snapshot
  "title": "string | null",
  "description": "string | null",
  "created_at": "datetime",
  "raw_url": "string",
  "structured_payload": "object | null"
}
```

---

## 📚 相关文档

- **[账号权限系统使用指南.md](./账号权限系统使用指南.md)** - 认证系统完整指南
- **[部署运维指南.md](./部署运维指南.md)**（待创建）- 部署和运维指南
- **[docs/02-技术文档/backend/工程结构API设计.md](../02-技术文档/backend/工程结构API设计.md)** - 工程结构 API 详细设计
- **[docs/02-技术文档/backend/账号权限系统完整指南.md](../02-技术文档/backend/账号权限系统完整指南.md)** - 认证系统技术细节

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-25
**维护者**: BDC-AI 开发团队
**状态**: ✅ 已完成
