# SQLite UUID 兼容性问题检查报告

**检查日期**: 2025-01-18
**问题类型**: SQLAlchemy UUID 类型与 SQLite 不兼容
**影响范围**: 10 处代码位置，3 个核心功能模块

---

## 📊 执行摘要

在开发环境使用 SQLite 时，发现 SQLAlchemy 的 `UUID(as_uuid=True)` 类型与 SQLite 存储格式存在严重兼容性问题，导致所有涉及 UUID 查询的接口无法正常工作。

### 核心问题
```
AttributeError: 'str' object has no attribute 'hex'
```

### 影响统计
- **受影响文件**: 3 个
- **问题代码位置**: 10 处
- **失效功能**: 6 个核心功能模块

---

## 🔍 问题分布

| 文件 | 问题数量 | 行号 | 严重程度 |
|------|---------|------|---------|
| `services/backend/app/api/v1/assets.py` | 4 处 | 53, 61, 78, 295 | 🔴 高 |
| `services/backend/app/api/v1/projects.py` | 3 处 | 57, 81, 111 | 🔴 高 |
| `services/backend/app/services/image_pipeline.py` | 3 处 | 62, 69, 198 | 🔴 高 |
| **总计** | **10 处** | | |

---

## 📁 详细问题清单

### 1. `services/backend/app/api/v1/assets.py` (4 处)

#### ❌ 问题 1.1：第 53 行 - `get_asset` 接口

**代码位置**：
```python
# 第 44-65 行
async def get_asset(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    from shared.db.models_asset import FileBlob

    # Convert UUID to string for SQLite compatibility
    asset_id_str = str(asset_id)  # 第 51 行

    asset = db.query(Asset).filter(Asset.id == asset_id_str).one_or_none()  # 第 53 行 - ❌ 错误
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    detail = AssetDetailRead.model_validate(asset)

    # Manually query file_blob to avoid SQLAlchemy relationship issues with SQLite
    if asset.file_id:
        file_blob = db.query(FileBlob).filter(FileBlob.id == str(asset.file_id)).one_or_none()  # 第 61 行 - ❌ 错误
        if file_blob is not None:
            detail.file_path = file_blob.path

    return detail
```

**影响**：
- Worker 无法获取 `file_path`
- 导致 GLM-4V Worker 无法读取本地图片
- 整个场景分析流程中断

**错误信息**：
```
AttributeError: 'str' object has no attribute 'hex'
[SQL: SELECT assets.id AS assets_id, ... FROM assets WHERE assets.id = ?]
[parameters: [{}]]
```

---

#### ❌ 问题 1.2：第 78 行 - `create_scene_issue_report` 接口

**代码位置**：
```python
# 第 73-80 行
@router.post(
    "/{asset_id}/scene_issue_report",
    response_model=AssetDetailRead,
    summary="Attach an LLM-based scene issue report to a scene_issue image asset",
)
async def create_scene_issue_report(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    report: SceneIssueReportPayload = Body(...),
    db: Session = Depends(get_db),
) -> AssetDetailRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()  # 第 78 行 - ❌ 错误
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
```

**影响**：
- GLM Worker 无法提交场景分析报告
- 分析结果无法回写到数据库
- `POST /api/v1/assets/{id}/scene_issue_report` 接口完全失效

---

#### ❌ 问题 1.3：第 295 行 - `run_ocr` 接口

**代码位置**：
```python
# 第 283-296 行
@router.post(
    "/{asset_id}/ocr",
    response_model=AssetStructuredPayload,
    summary="Manually trigger OCR for an image asset",
)
async def run_ocr(
    asset_id: uuid.UUID = Path(..., description="Asset ID"),
    db: Session = Depends(get_db),
) -> AssetStructuredPayload:
    try:
        structured: AssetStructuredPayload = process_image_with_ocr(db, asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # reload asset to return latest state
    asset = db.query(Asset).filter(Asset.id == asset_id).one()  # 第 295 行 - ❌ 错误
    return asset
```

**影响**：
- OCR 执行后无法刷新 Asset 状态
- 接口调用失败，无法获取更新后的资产状态

---

### 2. `services/backend/app/api/v1/projects.py` (3 处)

#### ❌ 问题 2.1：第 57 行 - `get_project` 接口

**代码位置**：
```python
# 第 47-63 行
@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
):
    project_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
    project = db.query(Project).filter(Project.id == project_uuid).first()  # 第 57 行 - ❌ 错误
```

**影响**：
- 无法查询单个项目详情
- `GET /api/v1/projects/{project_id}` 接口返回 500 错误

---

#### ❌ 问题 2.2：第 81 行 - `update_project` 接口

**代码位置**：
```python
# 第 71-89 行
@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
):
    project_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
    project = db.query(Project).filter(Project.id == project_uuid).first()  # 第 81 行 - ❌ 错误
```

**影响**：
- 无法更新项目信息
- `PUT /api/v1/projects/{project_id}` 接口返回 500 错误

---

#### ❌ 问题 2.3：第 111 行 - `delete_project` 接口

**代码位置**：
```python
# 第 101-118 行
@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
):
    project_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
    project = db.query(Project).filter(Project.id == project_uuid).first()  # 第 111 行 - ❌ 错误
```

**影响**：
- 无法删除项目
- `DELETE /api/v1/projects/{project_id}` 接口返回 500 错误

---

### 3. `services/backend/app/services/image_pipeline.py` (3 处)

#### ❌ 问题 3.1：第 62、69 行 - `_resolve_image_path` 函数

**代码位置**：
```python
# 第 42-77 行
def _resolve_image_path(db: Session, asset_or_id) -> Tuple[Asset, str]:
    """Resolve image path from an Asset instance or asset ID."""

    # Allow passing an already-loaded Asset to avoid extra queries
    if isinstance(asset_or_id, Asset):
        asset = asset_or_id
    else:
        # Normalise to uuid.UUID
        if isinstance(asset_or_id, uuid.UUID):
            asset_uuid = asset_or_id
        else:
            asset_uuid = uuid.UUID(str(asset_or_id))

        asset: Asset | None = db.query(Asset).filter(Asset.id == asset_uuid).one_or_none()  # 第 62 行 - ❌ 错误
        if asset is None:
            raise ValueError("Asset not found")

    if asset.modality != "image":
        raise ValueError("Asset modality must be 'image' for image parsing")

    file_blob: FileBlob | None = db.query(FileBlob).filter(FileBlob.id == asset.file_id).one_or_none()  # 第 69 行 - ❌ 错误
    if file_blob is None:
        raise ValueError("FileBlob not found for asset")
```

**影响**：
- OCR Pipeline 无法读取图片文件
- `process_image_with_ocr` 函数完全失效
- 图片自动路由（OCR 分支）无法执行

---

#### ❌ 问题 3.2：第 198 行 - `route_image_asset` 函数

**代码位置**：
```python
# 第 174-218 行
def route_image_asset(db: Session, asset_or_id) -> Asset:
    """Route an image asset to the appropriate pipeline based on content_role."""

    if asset_or_id is None:
        raise ValueError("Asset or asset_id cannot be empty")

    # Accept a pre-loaded Asset (e.g. immediately after upload) to avoid an
    # extra lookup, but also support being called from endpoints with an ID.
    if isinstance(asset_or_id, Asset):
        asset = asset_or_id
    else:
        if isinstance(asset_or_id, uuid.UUID):
            asset_uuid = asset_or_id
        else:
            asset_uuid = uuid.UUID(str(asset_or_id))

        asset: Asset | None = db.query(Asset).filter(Asset.id == asset_uuid).one_or_none()  # 第 198 行 - ❌ 错误
        if asset is None:
            raise ValueError("Asset not found")
```

**影响**：
- 图片自动路由功能完全失效
- `auto_route=true` 参数无法触发后续处理

---

## 🎯 根本原因分析

### UUID 类型在不同数据库中的存储差异

| 数据库 | UUID 存储方式 | Python 侧 | 查询兼容性 | 生产环境适用性 |
|--------|--------------|----------|-----------|---------------|
| **PostgreSQL** | 原生 uuid 类型 | uuid.UUID 对象 | ✅ 完全兼容 | ✅ 推荐 |
| **SQLite** | BLOB 或字符串（无连字符） | uuid.UUID 或 str | ❌ 格式不匹配 | ⚠️ 仅开发 |

### SQLite 中的实际存储格式

**数据库中存储**：
```sql
-- assets.id 实际存储（无连字符）
420c77fdcd8d40eea3faabed13243c2a

-- Python 传入（带连字符）
420c77fd-cd8d-40ee-a3fa-abed13243c2a
```

**测试验证**：
```bash
# 直接 SQL 查询（成功）
sqlite> SELECT * FROM assets WHERE id = '420c77fdcd8d40eea3faabed13243c2a';
-- 查询成功

# SQLAlchemy ORM 查询（失败）
db.query(Asset).filter(Asset.id == '420c77fd-cd8d-40ee-a3fa-abed13243c2a').one()
# AttributeError: 'str' object has no attribute 'hex'
```

### SQLAlchemy UUID 类型处理流程

```
用户传入 UUID 字符串
    ↓
SQLAlchemy 检测到 Asset.id 是 UUID(as_uuid=True) 列
    ↓
尝试将右侧值转换为 uuid.UUID 对象
    ↓
调用 .hex() 方法提取 UUID 的十六进制部分
    ↓
字符串没有 .hex() 方法 → 抛出 AttributeError
```

---

## 💥 功能影响矩阵

| 功能模块 | 当前状态 | 受影响接口 | 业务影响 |
|---------|---------|-----------|---------|
| **图片上传** | ✅ 正常 | `POST /assets/upload` | 无影响 |
| **图片自动路由** | ❌ 失效 | `upload_image_with_note?auto_route=true` | 无法触发 OCR/LLM |
| **OCR 文字识别** | ❌ 失效 | `POST /assets/{id}/ocr` | 无法手动触发 OCR |
| **GLM-4V 场景分析** | ❌ 失效 | `GET /assets/{id}` 返回 500 | Worker 无法读取 file_path |
| **项目查询** | ❌ 失效 | `GET /projects/{id}` | 无法查看项目详情 |
| **项目更新** | ❌ 失效 | `PUT /projects/{id}` | 无法更新项目 |
| **项目删除** | ❌ 失效 | `DELETE /projects/{id}` | 无法删除项目 |
| **Scene Issue 报告** | ❌ 失效 | `POST /assets/{id}/scene_issue_report` | 无法提交分析结果 |
| **Asset 详情查询** | ❌ 失效 | `GET /assets/{id}` | 500 错误 |

---

## 🔧 修复方案对比

### 方案 A：使用原始 SQL（✅ 推荐）

**原理**：绕过 SQLAlchemy 的 ORM 查询，直接使用原始 SQL

**优点**：
- ✅ 完全绕过 UUID 类型处理
- ✅ 兼容 SQLite 和 PostgreSQL
- ✅ 修改量可控，影响范围小
- ✅ 不需要改变数据库表结构

**缺点**：
- ⚠️ 代码可读性略降
- ⚠️ 需要手动映射结果到 ORM 对象

**实现示例**：
```python
from sqlalchemy import text

def get_asset(db: Session, asset_id: uuid.UUID) -> Asset:
    asset_id_str = str(asset_id)

    # 使用原始 SQL 查询
    query = text("SELECT * FROM assets WHERE id = :asset_id").params(asset_id=asset_id_str)
    result = db.execute(query).fetchone()

    if result is None:
        raise ValueError("Asset not found")

    # 手动映射结果到 Asset 对象
    asset = Asset(**result._mapping)
    return asset
```

**适用场景**：
- 开发环境使用 SQLite
- 快速修复，不改变架构
- 保持与 PostgreSQL 的兼容性

---

### 方案 B：移除 UUID 类型，改用 String（❌ 不推荐）

**原理**：模型定义中使用 `String(36)` 替代 `UUID(as_uuid=True)`

**优点**：
- ✅ ORM 查询正常工作
- ✅ SQLite 兼容性最好

**缺点**：
- ❌ 失去 UUID 类型检查
- ❌ 迁移到 PostgreSQL 时需重新修改
- ❌ 需要重建所有数据库表
- ❌ 可能影响已有数据

**实现示例**：
```python
class Asset(Base):
    # 改为 String 类型
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String(36), ForeignKey("file_blobs.id"))
```

**适用场景**：
- 仅适用于纯 SQLite 环境
- 不建议用于需要迁移到 PostgreSQL 的项目

---

### 方案 C：切换到 PostgreSQL（✅ 生产推荐）

**原理**：开发环境也使用 PostgreSQL

**优点**：
- ✅ 原生支持 UUID 类型
- ✅ 所有代码无需修改
- ✅ 符合生产环境要求
- ✅ 避免环境差异问题

**缺点**：
- ⚠️ 需要安装和配置 PostgreSQL
- ⚠️ 开发环境资源占用增加

**实施步骤**：
1. 安装 PostgreSQL
2. 创建数据库和用户
3. 修改 `.env` 配置：
   ```bash
   BDC_DATABASE_URL=postgresql://user:pass@localhost:5432/bdc_ai
   ```
4. 运行数据库迁移

**适用场景**：
- 生产环境部署
- 需要保证环境一致性
- 长期维护的项目

---

### 方案 D：使用混合方案（⚠️ 复杂但灵活）

**原理**：根据数据库类型动态选择查询方式

**优点**：
- ✅ 开发和生产都支持
- ✅ 代码有良好的兼容性

**缺点**：
- ❌ 代码复杂度增加
- ❌ 维护成本高

**实现示例**：
```python
from shared.config.settings import get_settings

settings = get_settings()

def get_asset(db: Session, asset_id: uuid.UUID) -> Asset:
    # 检测数据库类型
    is_postgres = "postgresql" in settings.database_url

    if is_postgres:
        # PostgreSQL：使用 ORM 查询
        asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    else:
        # SQLite：使用原始 SQL
        from sqlalchemy import text
        query = text("SELECT * FROM assets WHERE id = :asset_id").params(asset_id=str(asset_id))
        result = db.execute(query).fetchone()
        asset = Asset(**result._mapping) if result else None

    return asset
```

**适用场景**：
- 需要同时支持多种数据库
- 有充足的测试资源

---

## 📋 修复任务清单

### 需要修复的位置（10 处）

#### `services/backend/app/api/v1/assets.py`
- [ ] **第 53 行**：`get_asset` - Asset 查询
- [ ] **第 61 行**：`get_asset` - FileBlob 查询
- [ ] **第 78 行**：`create_scene_issue_report` - Asset 查询
- [ ] **第 295 行**：`run_ocr` - Asset 刷新查询

#### `services/backend/app/api/v1/projects.py`
- [ ] **第 57 行**：`get_project` - Project 查询
- [ ] **第 81 行**：`update_project` - Project 查询
- [ ] **第 111 行**：`delete_project` - Project 查询

#### `services/backend/app/services/image_pipeline.py`
- [ ] **第 62 行**：`_resolve_image_path` - Asset 查询
- [ ] **第 69 行**：`_resolve_image_path` - FileBlob 查询
- [ ] **第 198 行**：`route_image_asset` - Asset 查询

---

## 🧪 测试验证计划

### 1. 单元测试
```python
def test_get_asset_with_uuid():
    """测试 UUID 查询是否正常工作"""
    asset_id = uuid.uuid4()

    # 创建测试数据
    asset = Asset(id=asset_id, ...)
    db.add(asset)
    db.commit()

    # 测试查询
    result = get_asset(db, asset_id)
    assert result.id == asset_id
```

### 2. 集成测试
- [ ] 测试 `GET /api/v1/assets/{id}` 返回正确的 file_path
- [ ] 测试 `POST /api/v1/assets/{id}/scene_issue_report` 成功提交
- [ ] 测试 Worker 能够读取图片并调用 GLM-4V
- [ ] 测试 OCR 流程正常执行

### 3. 端到端测试
- [ ] 上传 scene_issue 图片（auto_route=true）
- [ ] 等待 Worker 处理
- [ ] 验证状态从 `pending_scene_llm` 变为 `parsed_scene_llm`
- [ ] 检查 `scene_issue_report_v1` payload 内容

---

## 📚 相关文档

- [SQLite UUID 文档](https://www.sqlite.org/c3ref/datatype_uuid.html)
- [SQLAlchemy UUID 类型](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Uuid)
- [PostgreSQL UUID 类型](https://www.postgresql.org/docs/current/datatype-uuid.html)

---

## 🎯 推荐修复方案

### 短期（开发环境）
**使用方案 A（原始 SQL）**：
- 快速修复所有 10 处问题
- 保持代码结构不变
- 验证功能恢复正常

### 长期（生产环境）
**使用方案 C（切换到 PostgreSQL）**：
- 避免环境差异
- 利用 PostgreSQL 原生 UUID 支持
- 提升生产环境稳定性

---

**报告生成时间**: 2025-01-18
**检查范围**: `services/backend/` 全部 Python 代码
**问题总数**: 10 处
**严重程度**: 🔴 高优先级
